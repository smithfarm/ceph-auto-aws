#
# Copyright (c) 2016, SUSE LLC
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# * Neither the name of ceph-auto-aws nor the names of its contributors may be
# used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import logging

from handson.keypair import Keypair
from handson.myyaml import stanza
from handson.region import Region
from handson.subnet import Subnet
from handson.tag import apply_tag
from handson.util import derive_ip_address, get_file_as_string

log = logging.getLogger(__name__)


class Delegate(Region):

    def __init__(self, args, delegate):
        super(Delegate, self).__init__(args)
        self.args = args
        k = Keypair(self.args, delegate)
        k.keypair_obj(import_ok=True, dry_run=self.args.dry_run)
        s = Subnet(self.args, delegate)
        s_obj = s.subnet_obj(create=True, dry_run=self.args.dry_run)
        ec2 = self.ec2()
        self._delegate = {
            'delegate': delegate,
            'ec2': ec2,
            'keyname': k.get_keyname_from_yaml(),
            'roles': {},
            'subnet_obj': s_obj,
        }

    def preexisting_instances(self):
        delegate = self._delegate['delegate']
        ec2 = self._delegate['ec2']
        s_obj = self._delegate['subnet_obj']
        s_id = s_obj.id
        instance_list = ec2.get_only_instances(
            filters={"subnet-id": s_id}
        )
        count = len(instance_list)
        if count > 0:
            log.warning("Delegate {} (subnet {}) already has {} instances"
                        .format(delegate, s_obj.cidr_block, count))
        return count

    def set_subnet_map_public_ip(self):
        """
            Attempts to set the MapPublicIpOnLaunch attribute to True.
            Code taken from http://stackoverflow.com/questions/25977048
            Author: Mark Doliner
        """
        ec2 = self._delegate['ec2']
        subnet_id = self._delegate['subnet_obj'].id
        orig_api_version = ec2.APIVersion
        ec2.APIVersion = '2014-06-15'
        ec2.get_status(
            'ModifySubnetAttribute',
            {'SubnetId': subnet_id, 'MapPublicIpOnLaunch.Value': 'true'},
            verb='POST'
        )
        ec2.APIVersion = orig_api_version
        return None

    def roles_to_install(self):
        delegate = self._delegate['delegate']
        rti = []
        if delegate == 0:
            role_def = self.assemble_role_def('master')
            self._delegate['roles']['master'] = role_def
            rti.append('master')
        if delegate > 0:
            cluster_def = stanza('cluster-definition')
            for cluster_def_entry in cluster_def:
                role = cluster_def_entry['role']
                role_def = self.assemble_role_def(role)
                self._delegate['roles'][role] = role_def
                rti.append(role)
        return rti

    def ready_to_install(self, dry_run=False):
        if self.preexisting_instances():
            return False
        if dry_run:
            return True
        rti = self.roles_to_install()
        log.info("Installing nodes: {!r}".format(rti))
        return True

    def assemble_role_def(self, role):
        rd = stanza('role-definitions')
        rv = rd['defaults']
        for a in rd[role]:
            rv[a] = rd[role][a]
        return rv

    def instantiate_role(self, role):
        delegate = self._delegate['delegate']
        ec2 = self._delegate['ec2']
        rd = self._delegate['roles'][role]
        private_ip = derive_ip_address(
            self._delegate['subnet_obj'].cidr_block,
            self._delegate['delegate'],
            rd['last-octet'],
        )
        # kwargs we use always
        our_kwargs = {
            "key_name": self._delegate['keyname'],
            "subnet_id": self._delegate['subnet_obj'].id,
            "instance_type": rd['type'],
            "private_ip_address": private_ip,
        }
        # conditional kwargs
        if rd['user-data']:
            material = get_file_as_string(rd['user-data'])
            log.info("Read {} characters of user-data from file {}"
                     .format(len(material), rd['user-data']))
            our_kwargs['user_data'] = material
        reservation = ec2.run_instances(rd['ami-id'], **our_kwargs)
        i_obj = reservation.instances[0]
        apply_tag(i_obj, tag='Name', val=stanza('nametag'))
        apply_tag(i_obj, tag='Role', val=role)
        apply_tag(i_obj, tag='Delegate', val=delegate)
        return i_obj

    def install(self, dry_run=False):
        if not self.ready_to_install(dry_run=dry_run):
            return None
        if dry_run:
            log.info("Dry run: doing nothing")
        delegate = self._delegate['delegate']
        c_stanza = stanza('clusters')
        c_stanza[delegate] = {}
        stanza('clusters', c_stanza)
        self.set_subnet_map_public_ip()
        for role in self._delegate['roles']:
            c_stanza[delegate][role] = {}
            stanza('clusters', c_stanza)
            i_obj = self.instantiate_role(role)
            c_stanza[delegate][role]['instance_id'] = i_obj.id
            stanza('clusters', c_stanza)
            log.info("Instantiated {} node (instance ID {})"
                     .format(role, i_obj.id))
        return None

    def walk_clusters(self, operation=None, dry_run=False):
        ec2 = self._delegate['ec2']
        delegate = self._delegate['delegate']
        c_stanza = stanza('clusters')
        if delegate not in c_stanza:
            log.warning("Delegate {} has no instances"
                        .format(delegate))
            return None

        if operation == "start":
            what_done = "started"
            do_what = ec2.start_instances
        elif operation == "stop":
            what_done = "stopped"
            do_what = ec2.stop_instances
        elif operation == "wipeout":
            what_done = "terminated"
            do_what = ec2.terminate_instances
        else:
            assert 1 == 0

        id_list = []
        for role in c_stanza[delegate]:
            if dry_run:
                log.info("Dry run: doing nothing for role {!r}"
                         .format(role))
                continue
            id_list.append(c_stanza[delegate][role]['instance_id'])
        if id_list:
            do_what(instance_ids=id_list)
        if operation == "wipeout" and not dry_run:
            del(c_stanza[delegate])
            stanza('clusters', c_stanza)
        log.info("{} instances {} for delegate {}"
                 .format(len(id_list), what_done, delegate))

    def wipeout(self, dry_run=False):
        self.walk_clusters(operation='wipeout', dry_run=dry_run)

    def stop(self, dry_run=False):
        self.walk_clusters(operation='stop', dry_run=dry_run)

    def start(self, dry_run=False):
        self.walk_clusters(operation='start', dry_run=dry_run)
