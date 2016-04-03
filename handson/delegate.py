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

from handson.myyaml import stanza
from handson.region import Region
from handson.subnet import Subnet
from handson.tag import apply_tag
from handson.util import derive_ip_address  # , read_user_data

log = logging.getLogger(__name__)


class Delegate(Region):

    def __init__(self, args, delegate):
        super(Delegate, self).__init__(args)
        self.args = args
        s = Subnet(self.args, delegate)
        s_obj = s.subnet_obj(create=True, dry_run=self.args.dry_run)
        ec2 = self.ec2()
        self._delegate = {
            'delegate': delegate,
            'ec2': ec2,
            'roles': {},
            'subnet_obj': s_obj,
        }

    def count_instances_in_subnet(self):
        ec2 = self._delegate['ec2']
        subnet_obj = self._delegate['subnet_obj']
        subnet_id = subnet_obj.id
        instance_list = ec2.get_only_instances(
            filters={"subnet-id": subnet_id}
        )
        return len(instance_list)

    def ready_to_install(self, dry_run=False):
        delegate = self._delegate['delegate']
        if dry_run:
            return True
        count = self.count_instances_in_subnet()
        if count > 0:
            log.warning("This delegate already has {} instances"
                        .format(count))
            return False
        roles_to_install = []
        if delegate == 0:
            role_def = self.assemble_role_def('master')
            self._delegate['roles']['master'] = role_def
            roles_to_install.append('master')
        if delegate > 0:
            cluster_def = stanza('cluster-definition')
            for cluster_def_entry in cluster_def:
                role = cluster_def_entry['role']
                role_def = self.assemble_role_def(role)
                self._delegate['roles'][role] = role_def
                roles_to_install.append(role)
        log.info("Installing nodes: {!r}".format(roles_to_install))
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
        our_kwargs = {
            "key_name": stanza('keyname'),
            "subnet_id": self._delegate['subnet_obj'].id,
            "instance_type": rd['type'],
            "private_ip_address": private_ip,
        }
        reservation = ec2.run_instances(rd['ami-id'], **our_kwargs)
        i_obj = reservation.instances[0]
        apply_tag(i_obj, tag='Name', val=stanza('nametag'))
        apply_tag(i_obj, tag='Role', val=role)
        apply_tag(i_obj, tag='Delegate', val=delegate)
        return i_obj

    def install(self, dry_run=False):
        delegate = self._delegate['delegate']
        if not self.ready_to_install(dry_run=dry_run):
            return None
        c_stanza = stanza('clusters')
        c_stanza[delegate] = {}
        stanza('clusters', c_stanza)
        for role in self._delegate['roles']:
            if dry_run:
                log.info("Dry run: doing nothing for role {!r}"
                         .format(role))
                continue
            c_stanza[delegate][role] = {}
            stanza('clusters', c_stanza)
            i_obj = self.instantiate_role(role)
            c_stanza[delegate][role]['instance_id'] = i_obj.id
            stanza('clusters', c_stanza)
            log.info("Instantiated {} node (instance ID {})"
                     .format(role, i_obj.id))

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
