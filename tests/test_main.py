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
from mock import patch
import unittest

from handson import main
from handson import myyaml


def mock_connect_ec2():
    return 'DummyValue'


class TestHandsOn(unittest.TestCase):

    def test_init(self):
        w = main.HandsOn()

        with self.assertRaises(SystemExit) as cm:
            w.parser.parse_args([
                '-h',
            ])
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            w.parser.parse_args([
                '--version',
            ])
        self.assertEqual(cm.exception.code, 0)

    @patch('boto.connect_ec2', side_effects=mock_connect_ec2)
    def test_test_credentials(self, mock_connect_ec2):
        m = main.HandsOn()

        self.assertTrue(
            m.run([
                '-v',
                'test-credentials',
            ])
        )
        l = logging.getLogger('handson')
        self.assertIs(l.getEffectiveLevel(), logging.DEBUG)

        self.assertTrue(
            m.run([
                'test-credentials',
            ])
        )
        l = logging.getLogger('handson')
        self.assertIs(l.getEffectiveLevel(), logging.INFO)
        l.info("Henry VIII")

    def test_test_yaml(self):
        m = main.HandsOn()

        with self.assertRaises(myyaml.YamlError):
            myyaml.myyaml.tree()

        self.assertTrue(
            m.run([
                'test-yaml',
            ])
        )
        self.assertTrue('region' in myyaml.myyaml.tree())
        self.assertTrue('vpc' in myyaml.myyaml.tree())
        self.assertTrue('keyname' in myyaml.myyaml.tree())

        del(myyaml._ss['file_name'])
        with self.assertRaises(IOError):
            m.run([
                '-y',
                'BogusFileThatDoesNotExist',
                'test-yaml',
            ])
