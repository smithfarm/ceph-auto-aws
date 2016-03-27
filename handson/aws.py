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
import boto
import boto.ec2
import boto.vpc
import myyaml


class AWS(myyaml.MyYaml):

    def __init__(self, yamlfile):
        self._aws = {}
        super(AWS, self).__init__(yamlfile)

    def ping_ec2(self):
        print "calling boto.connect_ec2"
        boto.connect_ec2()

    def ec2(self):
        tree = self.tree()
        if 'ec2' not in self._aws:
            self._aws['ec2'] = boto.ec2.connect_to_region(tree['region'])
        return self._aws['ec2']

    def vpc(self):
        tree = self.tree()
        if 'vpc' not in self._aws:
            self._aws['vpc'] = boto.vpc.connect_to_region(tree['region'])
        return self._aws['vpc']

    def vpc_obj(self):
        if 'vpc_obj' in self._aws:
            return self._aws['vpc_obj']
        tree = self.tree()
        vpc = self.vpc()
        if 'id' in tree['vpc']:
            vpc_id = tree['vpc']['id']
            vpc_list = vpc.get_all_vpcs(vpc_ids=vpc_id)
            self._aws['vpc_obj'] = vpc_list[0]
        else:  # pragma: no cover
            # create a new 10.0.0.0/16
            self._aws['vpc_obj'] = vpc.create_vpc('10.0.0.0/16')
            tree['vpc']['id'] = self._aws['vpc_obj'].id
            tree['vpc']['cidr_block'] = self._aws['vpc_obj'].cidr_block
            self.write()
        return self._aws['vpc_obj']
