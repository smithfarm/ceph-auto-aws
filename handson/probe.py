#
# Copyright (c) 2016, SUSE LLC All rights reserved.
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

import argparse
import logging

from handson.aws import AWS
from handson.error import YamlError
from handson.myyaml import myyaml

log = logging.getLogger(__name__)


class ProbeAWS(object):

    def __init__(self, args):
        self.args = args

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(
            parents=[],
            conflict_handler='resolve',
        )
        return parser

    def run(self):
        AWS().ping_ec2()
        print "Successfully connected to AWS EC2!"
        return True


class ProbeVPC(object):

    def __init__(self, args):
        self.args = args

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(
            parents=[],
            conflict_handler='resolve',
        )
        return parser

    def run(self):
        o = AWS().vpc_obj()
        print "VPC ID is {0!r}".format(o.id)


class ProbeYaml(object):

    def __init__(self, args):
        self.args = args

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(
            parents=[],
            conflict_handler='resolve',
        )
        return parser

    def run(self):
        myyaml.load()
        print "Loaded yaml from {}".format(myyaml.yaml_file_name())
        tree = myyaml.tree()
        try:
            fodder = ['region', 'vpc', 'keyname', 'nametag']
            for elem in fodder:
                assert elem in tree
        except AssertionError:
            raise YamlError(
                "Missing stanza in yaml file: {}".format(elem)
            )
        return True
