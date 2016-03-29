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
import unittest

from handson.error import HandsOnError, YamlError
from handson import main
from mock import patch
from yaml.parser import ParserError


def mock_connect(*_):
    return 'DummyValue'


def mock_connect_ec2(*_):
    return 'DummyValue'


class MockMyYaml(object):

    def write(self):
        return True


class MockVPCConnection(object):

    def create_vpc(self, *_):
        return {'id': 'DummyID', 'cidr_block': '10.0.0.0/16'}

    def get_all_vpcs(self, *_):
        return ['DummyValue']


class TestHandsOn(unittest.TestCase):

    def test_init(self):
        m = main.HandsOn()

        with self.assertRaises(SystemExit) as cm:
            m.parser.parse_args([
                '-h',
            ])
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            m.parser.parse_args([
                '--version',
            ])
        self.assertEqual(cm.exception.code, 0)

    def test_install(self):
        m = main.HandsOn()

        with self.assertRaises(HandsOnError):
            m.run([
                '-v', 'install', '1-50',
            ])

        with self.assertRaises(HandsOnError):
            m.run([
                'install', '51',
            ])

        with self.assertRaises(HandsOnError):
            m.run([
                'install', 'FartOnTheWater',
            ])

        with self.assertRaises(HandsOnError):
            m.run([
                'install', '0,1,3',
            ])

        with self.assertRaises(HandsOnError):
            m.run([
                'install', '1,3-2',
            ])

        with self.assertRaises(SystemExit) as cm:
            m.run([
                'install',
            ])
        self.assertEqual(cm.exception.code, 0)

    @patch('boto.connect_ec2', side_effects=mock_connect_ec2)
    def test_probe_aws(self, mock_connect_ec2):
        m = main.HandsOn()

        with self.assertRaises(SystemExit) as cm:
            m.run([
                '-v', 'probe', 'aws',
            ])
        self.assertEqual(cm.exception.code, 0)
        l = logging.getLogger('handson')
        self.assertIs(l.getEffectiveLevel(), logging.DEBUG)

        with self.assertRaises(SystemExit) as cm:
            m.run([
                'probe', 'aws',
            ])
        self.assertEqual(cm.exception.code, 0)
        l = logging.getLogger('handson')
        self.assertIs(l.getEffectiveLevel(), logging.INFO)

    def test_probe_cluster_definition(self):
        m = main.HandsOn()
        with self.assertRaises(SystemExit) as cm:
            m.run([
                'probe', 'cluster-definition',
            ])
        self.assertEqual(cm.exception.code, 0)

    def test_probe_role_definitions(self):
        m = main.HandsOn()
        with self.assertRaises(SystemExit) as cm:
            m.run([
                'probe', 'role-definitions',
            ])
        self.assertEqual(cm.exception.code, 0)

    def test_probe_subnets(self):
        m = main.HandsOn()

        with self.assertRaises(SystemExit) as cm:
            m.run([
                'probe', 'subnets',
            ])
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            m.run([
                'probe', 'subnets', '--retag',
            ])
        self.assertEqual(cm.exception.code, 0)

    def test_probe_types(self):
        m = main.HandsOn()

        with self.assertRaises(SystemExit) as cm:
            m.run([
                'probe', 'types',
            ])
        self.assertEqual(cm.exception.code, 0)

    def test_probe_vpc(self):
        m = main.HandsOn()

        with self.assertRaises(SystemExit) as cm:
            m.run([
                'probe', 'vpc',
            ])
        self.assertEqual(cm.exception.code, 0)

    def test_probe_yaml(self):
        m = main.HandsOn()

        with self.assertRaises(SystemExit) as cm:
            m.run([
                'probe', 'yaml',
            ])
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(IOError):
            m.run([
                '-y', 'BogusFileThatDoesNotExist',
                'probe', 'yaml',
            ])

        with self.assertRaises(ParserError):
            m.run([
                '-y', './bootstrap',
                'probe', 'yaml',
            ])

        with self.assertRaises(YamlError):
            m.run([
                '-y', './data/bogus.yaml',
                'probe', 'yaml',
            ])
