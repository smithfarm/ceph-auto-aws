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
import logging
import myyaml
import sys
import time

from handson.error import HandsOnError

log = logging.getLogger(__name__)


class AWS(myyaml.MyYaml):

    def __init__(self, yamlfile):
        self._aws = {}
        super(AWS, self).__init__(yamlfile)

    def ping_ec2(self):
        """
            used by probe-aws subcommand
        """
        boto.connect_ec2()  # raises exception on failure

    def region(self):
        """
            gets region from yaml, default to eu-west-1
        """
        tree = self.tree()
        if (
            'region' not in tree or
            tree['region'] is None
        ):  # pragma: no cover
            tree['region'] = 'eu-west-1'
            self.write()
            log.info("Region was missing: set to eu-west-1")
        log.debug("Region is {}".format(tree['region']))
        return tree['region']

    def ec2(self):
        """
            fetch ec2 connection, open if necessary
        """
        region = self.region()
        if 'ec2' not in self._aws or self._aws['ec2'] is None:
            log.debug("Connecting to EC2 region {}".format(region))
            self._aws['ec2'] = boto.ec2.connect_to_region(region)
        if self._aws['ec2'] is None:  # pragma: no cover
            raise HandsOnError("Failed to connect to {}".format(region))
        return self._aws['ec2']

    def vpc(self):
        """
            fetch vpc connection, open if necessary
        """
        region = self.region()
        if 'vpc' not in self._aws or self._aws['vpc'] is None:
            log.debug("Connecting to VPC region {}".format(region))
            self._aws['vpc'] = boto.vpc.connect_to_region(region)
        if self._aws['vpc'] is None:  # pragma: no cover
            raise HandsOnError("Failed to connect to {}".format(region))
        return self._aws['vpc']

    def apply_tag(self, obj, tag='Name', val=None):
        """
            tag an AWS object
        """
        for x in [1, 1, 2, 4, 8]:
            error = False
            try:
                obj.add_tag(tag, val)
            except:  # pragma: no cover
                error = True
                e = sys.exc_info()[0]
                log.info("Huh, trying again ({})".format(e))
                time.sleep(x)
            if not error:
                log.info("Object {} successfully tagged.".format(obj))
                break
        return None

    def vpc_obj(self):
        """
            fetch VPC object, create if necessary
        """
        #
        # cached VPC object
        if 'vpc_obj' in self._aws:
            return self._aws['vpc_obj']
        #
        # non-cached
        tree = self.tree()
        vpc = self.vpc()
        if (
                tree['vpc'] is None or
                'id' not in tree['vpc'] or
                tree['vpc']['id'] is None
        ):  # pragma: no cover
            log.debug("VPC ID not specified in yaml: creating VPC")
            self._aws['vpc_obj'] = vpc.create_vpc('10.0.0.0/16')
            tree['vpc'] = {}
            tree['vpc']['id'] = self._aws['vpc_obj'].id
            tree['vpc']['cidr_block'] = self._aws['vpc_obj'].cidr_block
            self.write()
            log.info("VPC created".format(
                tree['vpc']['id'], tree['vpc']['cidr_block']
            ))
        else:
            log.debug("VPD ID specified in yaml: fetching it")
            vpc_id = tree['vpc']['id']
            log.info("VPC ID according to yaml is {}".format(vpc_id))
            vpc_list = vpc.get_all_vpcs(vpc_ids=vpc_id)
            if len(vpc_list) == 0:  # pragma: no cover
                raise HandsOnError(
                    "VPC ID {} does not exist".format(vpc_id)
                )
            if len(vpc_list) > 1:  # pragma: no cover
                raise HandsOnError(
                    "Multiple VPCs with VPC ID {} (???)"
                    .format(vpc_id)
                )
            self._aws['vpc_obj'] = vpc_list[0]
            cidr_block = self._aws['vpc_obj'].cidr_block
            if cidr_block != '10.0.0.0/16':  # pragma: no cover
                m = ("VPC ID {} exists, but has wrong CIDR block {} "
                     "(should be 10.0.0.0/16)")
                raise HandsOnError(m.format(vpc_id, cidr_block))
        log.info("VPC ID is {}, CIDR block is {}".format(
            tree['vpc']['id'],
            tree['vpc']['cidr_block'],
        ))
        self.apply_tag(self._aws['vpc_obj'], tag='Name', val=tree['nametag'])
        return self._aws['vpc_obj']
