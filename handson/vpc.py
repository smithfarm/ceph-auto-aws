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
from handson.tag import apply_tag
# from handson.util import read_user_data

log = logging.getLogger(__name__)


class VPC(Region):

    def __init__(self, args):
        super(VPC, self).__init__(args)
        self.args = args
        self._vpc = {
            'vpc_obj': None
        }

    def vpc_obj(self):
        """
            fetch VPC object, create if necessary
        """
        #
        # cached VPC object
        if self._vpc['vpc_obj'] is not None:
            return self._vpc['vpc_obj']
        #
        # non-cached
        vpc_stanza = stanza('vpc')
        vpc_conn = self.vpc()
        if len(vpc_stanza) == 0:  # pragma: no cover
            #
            # create VPC
            log.debug("VPC ID not specified in yaml: creating VPC")
            vpc_obj = vpc_conn.create_vpc('10.0.0.0/16')
            vpc_stanza['id'] = vpc_obj.id
            vpc_stanza['cidr_block'] = vpc_obj.cidr_block
            log.info("New VPC ID {} created with CIDR block {}".format(
                vpc_obj.id, vpc_obj.cidr_block
            ))
            apply_tag(vpc_obj, tag='Name', val=stanza('nametag'))
            self._vpc['vpc_obj'] = vpc_obj
            stanza('vpc', {
                'cidr_block': vpc_obj.cidr_block,
                'id': vpc_obj.id
            })
            return vpc_obj
        #
        # existing VPC
        log.debug("VPD ID specified in yaml: fetching it")
        vpc_id = vpc_stanza['id']
        log.info("VPC ID according to yaml is {}".format(vpc_id))
        vpc_list = vpc_conn.get_all_vpcs(vpc_ids=vpc_id)
        assert len(vpc_list) == 1, (
               "VPC ID {} does not exist".format(vpc_id))
        vpc_obj = vpc_list[0]
        cidr_block = vpc_obj.cidr_block
        assert cidr_block == '10.0.0.0/16', (
               ("VPC ID {} exists, but has wrong CIDR block {} "
                "(should be 10.0.0.0/16)").format(vpc_id, cidr_block))
        log.info("VPC ID is {}, CIDR block is {}".format(
            vpc_stanza['id'], vpc_stanza['cidr_block'],
        ))
        self._vpc['vpc_obj'] = vpc_obj
        return vpc_obj
