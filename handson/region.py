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
import boto.ec2
import boto.vpc
import logging

from handson.myyaml import stanza
# from handson.util import read_user_data

log = logging.getLogger(__name__)


class Region(object):

    def __init__(self, args):
        self.args = args
        self._region = {
            'ec2_conn': None,
            'region_str': None,
            'vpc_conn': None,
            'availability_zone': None
        }

    def region(self):
        """
            gets region from yaml, default to eu-west-1
        """
        if self._region['region_str']:
            return self._region['region_str']
        self._region['region_str'] = stanza('region')
        log.debug("Region is {}".format(self._region['region_str']))
        return self._region['region_str']

    def ec2(self):
        """
            fetch ec2 connection, open if necessary
        """
        if self._region['ec2_conn']:
            return self._region['ec2_conn']
        region = self.region()
        if self._region['ec2_conn'] is None:
            log.debug("Connecting to EC2 region {}".format(region))
            self._region['ec2_conn'] = boto.ec2.connect_to_region(
                region,
                is_secure=False
            )
        assert self._region['ec2_conn'] is not None, (
               ("Failed to connect to EC2 service in region {!r}"
                .format(region)))
        return self._region['ec2_conn']

    def vpc(self):
        """
            fetch vpc connection, open if necessary
        """
        if self._region['vpc_conn']:
            return self._region['vpc_conn']
        region = self.region()
        if self._region['vpc_conn'] is None:
            log.debug("Connecting to VPC region {}".format(region))
            self._region['vpc_conn'] = boto.vpc.connect_to_region(
                region,
                is_secure=False
            )
        assert self._region['vpc_conn'] is not None, (
               ("Failed to connect to VPC service in region {!r}"
                .format(region)))
        return self._region['vpc_conn']
