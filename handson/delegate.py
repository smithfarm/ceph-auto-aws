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
import copy
import logging
import time

from handson.keypair import Keypair
from handson.myyaml import stanza
from handson.region import Region
from handson.subnet import Subnet
from handson.tag import apply_tag
from handson.util import (
    derive_ip_address,
    get_file_as_string,
    template_token_subst,
)

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

    def apply_tags(self, aws_obj, role=None):
        delegate = self._delegate['delegate']
        apply_tag(aws_obj, tag='Name', val=stanza('nametag'))
        apply_tag(aws_obj, tag='Role', val=role)
        apply_tag(aws_obj, tag='Delegate', val=delegate)

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
        rdd = {}
        if delegate == 0:
            role_def = self.assemble_role_def('master')
            rdd['master'] = role_def
            rti.append('master')
        if delegate > 0:
            cluster_def = stanza('cluster-definition')
            for cluster_def_entry in cluster_def:
                role = cluster_def_entry['role']
                role_def = self.assemble_role_def(role)
                rdd[role] = role_def
                rti.append(role)
        return (rti, rdd)

    def ready_to_install(self, dry_run=False):
        if self.preexisting_instances():
            return False
        if dry_run:
            return True
        (rti, self._delegate['role_defs']) = self.roles_to_install()
        return rti

    def assemble_role_def(self, role):
        rd = stanza('role-definitions')
        rv = copy.deepcopy(rd['defaults'])
        for a in rd[role]:
            rv[a] = rd[role][a]
        return rv

    def instantiate_role(self, role):
        delegate = self._delegate['delegate']
        ec2 = self._delegate['ec2']
        rd = self._delegate['role_defs'][role]
        log.info("Instantiating role {} from role-def {!r}".format(role, rd))
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
            u = get_file_as_string(rd['user-data'])
            log.info("Read {} characters of user-data from file {}"
                     .format(len(u), rd['user-data']))
            # FIXME master IP address is hardcoded
            # FIXME template_token_subst() calls are hardcoded
            u = template_token_subst(u, '@@MASTER_IP@@', '10.0.0.10')
            u = template_token_subst(u, '@@DELEGATE@@', delegate)
            u = template_token_subst(u, '@@ROLE@@', role)
            u = template_token_subst(u, '@@NODE_NO@@', rd['node-no'])
            our_kwargs['user_data'] = u
        reservation = ec2.run_instances(rd['ami-id'], **our_kwargs)
        i_obj = reservation.instances[0]
        self.apply_tags(i_obj, role=role)
        v_obj = None
        if rd['volume']:
            vol_size = int(rd['volume'])
            log.info("Role {} requires {}GB volume".format(role, vol_size))
            if vol_size > 0:
                v_obj = ec2.create_volume(vol_size, i_obj.placement)
                self.apply_tags(v_obj, role=role)
        return (i_obj, v_obj)

    def instance_await_state(self, role, instance_id, state='running'):
        return self.await_state(
            role,
            instance_id,
            state=state,
            thing='instance'
        )

    def volume_await_state(self, role, volume_id, state='running'):
        return self.await_state(
            role,
            volume_id,
            state=state,
            thing='volume'
        )

    def await_state(self, role, t_id, thing=None, state=None):
        log.info("Waiting for {} {} to reach '{}' state"
                 .format(role, thing, state))
        ec2 = self._delegate['ec2']
        while True:
            if thing == 'instance':
                things = ec2.get_only_instances(instance_ids=[t_id])
                aws_state = things[0].state
            elif thing == 'volume':
                things = ec2.get_all_volumes(volume_ids=[t_id])
                aws_state = things[0].status
            else:
                assert 1 == 0, "Programmer brain failure"
            log.info("Current state is {}".format(aws_state))
            if aws_state != state:
                log.info("Sleeping for 5 seconds")
                time.sleep(5)
            else:
                # log.info("Sleeping another 5 seconds for good measure"
                # time.sleep(5)
                break

    def install(self, dry_run=False):
        self._delegate['roles'] = self.ready_to_install(dry_run=dry_run)
        if not self._delegate['roles']:
            return None
        if dry_run:
            log.info("Dry run: doing nothing")
        delegate = self._delegate['delegate']
        c_stanza = stanza('clusters')
        c_stanza[delegate] = {}
        stanza('clusters', c_stanza)
        self.set_subnet_map_public_ip()
        # instantiate node for each role
        aws_objs = {}
        for role in self._delegate['roles']:
            c_stanza[delegate][role] = {}
            stanza('clusters', c_stanza)
            (i_obj, v_obj) = self.instantiate_role(role)
            aws_objs[role] = {}
            aws_objs[role]['instance_obj'] = i_obj
            aws_objs[role]['volume_obj'] = v_obj
            c_stanza[delegate][role]['instance_id'] = i_obj.id
            c_stanza[delegate][role]['placement'] = i_obj.placement
            if v_obj:
                c_stanza[delegate][role]['volume_id'] = v_obj.id
            stanza('clusters', c_stanza)
            log.info("Instantiated {} node (instance ID {})"
                     .format(role, i_obj.id))
        # attach volumes
        ec2 = self._delegate['ec2']
        for role in self._delegate['roles']:
            i_obj = aws_objs[role]['instance_obj']
            v_obj = aws_objs[role]['volume_obj']
            if v_obj:
                c_stanza[delegate][role]['volume_id'] = v_obj.id
                self.instance_await_state(role, i_obj.id, state='running')
                self.volume_await_state(role, v_obj.id, state='available')
                assert ec2.attach_volume(v_obj.id, i_obj.id, '/dev/sdb'), (
                    "Failed to attach volume to role {}, delegate {}"
                    .format(role, delegate))
        return None

    def is_attached(self, v_id, i_id):
        ec2 = self._delegate['ec2']
        attached_vol = ec2.get_all_volumes(
            filters={
                "volume-id": v_id,
                "attachment.instance-id": i_id,
                "attachment.device": "/dev/sdb"
            }
        )
        log.debug("attached_vol == {}".format(attached_vol))
        if attached_vol is None or len(attached_vol) == 0:
            return False
        return True

    def wait_for_detachment(self, v_id, i_id):
        log.info("Waiting for volume {} to be detached from instance {}"
                 .format(v_id, i_id))
        while True:
            if self.is_attached(v_id, i_id):
                time.sleep(5)
                log.info("Still attached")
                continue
            log.info("Volume has been detached")
            break

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

        instance_id_list = []
        iv_map = {}  # keys are instance IDs and values are volume IDs
        for role in c_stanza[delegate]:
            if dry_run:
                log.info("Dry run: doing nothing for role {!r}"
                         .format(role))
                continue
            i_id = c_stanza[delegate][role]['instance_id']
            instance_id_list.append(i_id)
            if 'volume_id' in c_stanza[delegate][role]:
                iv_map[i_id] = {
                    'volume_id': c_stanza[delegate][role]['volume_id'],
                    'role': role
                }
        if operation == "wipeout" and iv_map:
            ec2.stop_instances(instance_ids=iv_map.keys())
            # for i_id in iv_map.keys():
            #     self.instance_await_state(
            #         iv_map[i_id]['role'],
            #         i_id,
            #         state='stopped',
            #     )
            log.info("Detaching {} volumes...".format(len(iv_map)))
            for i_id in iv_map.keys():
                v_id = iv_map[i_id]['volume_id']
                v_list = ec2.get_all_volume_status(volume_ids=[v_id])
                log.debug("Volume {} status {}"
                          .format(v_id, v_list[0].__dict__))
                if self.is_attached(v_id, i_id):
                    ec2.detach_volume(
                        v_id,
                        instance_id=i_id,
                        device='/dev/sdb',
                        force=True
                    )
            log.info("Deleting {} volumes...".format(len(iv_map)))
            for i_id in iv_map.keys():
                v_id = iv_map[i_id]['volume_id']
                self.wait_for_detachment(v_id, i_id)
                ec2.delete_volume(v_id)
        if instance_id_list:
            do_what(instance_ids=instance_id_list)
        if operation == "wipeout" and not dry_run:
            del(c_stanza[delegate])
            stanza('clusters', c_stanza)
        log.info("{} instances {} for delegate {}"
                 .format(len(instance_id_list), what_done, delegate))

    def wipeout(self, dry_run=False):
        self.walk_clusters(operation='wipeout', dry_run=dry_run)

    def stop(self, dry_run=False):
        self.walk_clusters(operation='stop', dry_run=dry_run)

    def start(self, dry_run=False):
        self.walk_clusters(operation='start', dry_run=dry_run)

    def fetch_public_ip(self, role):
        ec2 = self._delegate['ec2']
        subnet_id = self._delegate['subnet_obj'].id
        instances = ec2.get_only_instances(
            filters={
                "subnet-id": subnet_id,
                "tag-key": "Role",
                "tag-value": role
            }
        )
        found = False
        public_ip = ''
        for i in instances:
            public_ip = "{}".format(i.ip_address)
            found = True
        if not found:
            public_ip = "(none)"
        return public_ip

    def probe(self):
        delegate = self._delegate['delegate']
        c_stanza = stanza('clusters')
        if delegate not in c_stanza:
            log.info("Delegate {} not instantiated".format(delegate))
            return None
        d_stanza = c_stanza[delegate]
        retval = False
        for role in d_stanza.keys():
            retval = True
            log.info("Delegate {}, role {}, public IP {}"
                     .format(delegate, role, self.fetch_public_ip(role)))
        return retval

    def public_ips(self):
        delegate = self._delegate['delegate']
        c_stanza = stanza('clusters')
        public_ips = {}
        if delegate not in c_stanza:
            log.info("Delegate {} not instantiated".format(delegate))
            return None
        d_stanza = c_stanza[delegate]
        for role in d_stanza.keys():
            public_ips[role] = self.fetch_public_ip(role)
        return public_ips
