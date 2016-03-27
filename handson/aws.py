# -*- mode: python; coding: utf-8 -*-
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
from boto import connect_ec2, ec2, vpc
from handson.myyaml import myyaml

_ss = {}  # saved state


class AWS(object):

    def ping_ec2(self):
        connect_ec2()

    def ec2(self):
        tree = myyaml.tree()
        if 'ec2' not in _ss:
            _ss['ec2'] = ec2.connect_to_region(tree['region'])
        return _ss['ec2']

    def vpc(self):
        tree = myyaml.tree()
        if 'vpc' not in _ss:
            _ss['vpc'] = vpc.connect_to_region(tree['region'])
        return _ss['vpc']

    def vpc_obj(self):
        if 'vpc_obj' in _ss:
            return _ss['vpc_obj']
        tree = myyaml.tree()
        vpc = self.vpc()
        if 'id' in tree['vpc']:
            vpc_id = tree['vpc']['id']
            vpc_list = vpc.get_all_vpcs(vpc_ids=vpc_id)
            _ss['vpc_obj'] = vpc_list[0]
            return _ss['vpc_obj']
        # create a new 10.0.0.0/16
        _ss['vpc_obj'] = vpc.create_vpc('10.0.0.0/16')
        tree['vpc']['id'] = _ss['vpc_obj'].id
        tree['vpc']['cidr_block'] = _ss['vpc_obj'].cidr_block
        myyaml.write()
        return _ss['vpc_obj']

aws = AWS()
