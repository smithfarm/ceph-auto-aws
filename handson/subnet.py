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
from handson.tag import apply_tag
# from handson.util import read_user_data
from handson.vpc import VPC

log = logging.getLogger(__name__)


class Subnet(VPC):

    def __init__(self, args, delegate):
        super(Subnet, self).__init__(args)
        self.args = args
        self._subnet = {
            'delegate': delegate,
            's_obj': None
        }

    def subnet_obj(self):
        """
            Subnet object is returned from cache if cached.
            Otherwise, the method validates the subnet, creates it if
            necessary, populates tree, and returns subnet object.
        """
        if self._subnet['s_obj']:
            return self._subnet['s_obj']
        s_stanza = stanza('subnets')
        vpc = self.vpc()
        vpc_obj = self.vpc_obj(create=False)
        args = self.args
        delegate = self._subnet['delegate']
        cidr_block = '10.0.{}.0/24'.format(delegate)
        if delegate not in s_stanza:  # pragma: no cover
            s_stanza[delegate] = {}
            #
            # create new subnet
            log.debug("About to create subnet {}".format(cidr_block))
            s_obj = vpc.create_subnet(vpc_obj.id, cidr_block)
            log.info(
                "Created subnet {} ({})".format(s_obj.id, s_obj.cidr_block)
            )
            s_stanza[delegate]['cidr_block'] = s_obj.cidr_block
            s_stanza[delegate]['id'] = s_obj.id
            stanza('subnets', s_stanza)
            apply_tag(s_obj, tag='Name', val=stanza('nametag'))
            apply_tag(s_obj, tag='Delegate', val=delegate)
            self._subnet['s_obj'] = s_obj
            return s_obj
        #
        # check id exists and cidr_block matches
        s_id = s_stanza[delegate]['id']
        log.debug("Getting subnet id {}".format(s_id))
        s_list = vpc.get_all_subnets(subnet_ids=[s_id])
        assert len(s_list) == 1, "Subnet ID {} does not exist".format(s_id)
        s_obj = s_list[0]
        log.info("Found subnet {} ({})".format(s_obj.id, s_obj.cidr_block))
        if (
             'cidr_block' not in s_stanza[delegate] or
             s_stanza[delegate]['cidr_block'] is None
        ):  # pragma: no cover
            #
            # set cidr_block
            s_stanza[delegate]['cidr_block'] = s_obj.cidr_block
            stanza('subnets', s_stanza)
        else:
            #
            # validate cidr_block
            assert s_stanza[delegate]['cidr_block'] == s_obj.cidr_block, (
                ("Delegate {} is supposed to have subnet {}, but that "
                 "subnet exists with non-matching CIDR block {}")
                .format(
                    delegate,
                    s_stanza[delegate]['cidr_block'],
                    s_obj.cidr_block
                ))
        self._subnet['s_obj'] = s_obj
        if args.retag:
            apply_tag(s_obj, tag='Name', val=stanza('nametag'))
            apply_tag(s_obj, tag='Delegate', val=delegate)
        return s_obj
