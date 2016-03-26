# -*- mode: python; coding: utf-8 -*-
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
import textwrap
from testcred import TestCredentials
from testyaml import TestYaml
from myyaml import myyaml

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')

__version__ = "0.0.12"


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass


class YamlFileAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        print 'option_string: {0!r}'.format(option_string)
        if option_string == '-y' or option_string == '--yamlfile':
            print 'value: {0!r}'.format(values)
            myyaml.yaml_file_name(values)


class HandsOn(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Scripting for hands-on demonstrations of Ceph.

            The documentation for each subcommand can be displayed with

               ho subcommand --help

            For instance:

               ho test-credentials --help
               usage: ho test-credentials [-h]
               ...

            For more information, refer to the README.rst file at
            https://github.com/smithfarm/ceph-auto-aws/README.rst
            """))

        self.parser.add_argument(
            '-v', '--verbose',
            action='store_true', default=None,
            help='be more verbose',
        )

        self.parser.add_argument(
            '--version',
            action='version', version=__version__,
            help='print version number',
        )

        self.parser.add_argument(
            '-y', '--yamlfile',
            default='./aws.yaml',
            action=YamlFileAction,
            help='specify yaml file to read',
        )

        subparsers = self.parser.add_subparsers(
            title='subcommands',
            description='valid subcommands',
            help='sub-command -h',
        )

        subparsers.add_parser(
            'test-credentials',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Test AWS EC2 credentials.

            Once you have set up your AWS credentials in ~/.boto,
            run this subcommand to check connectivity.
            """),
            epilog=textwrap.dedent("""
            Examples:

            $ ho test-credentials
            $ echo $?
            0

            $ ho test-credentials
            2016-03-26 01:09:08 ERROR Caught exception reading instance data
            ...
            $ echo $?
            1

            """),
            help='Test AWS EC2 credentials',
            parents=[TestCredentials.get_parser()],
            add_help=False,
        ).set_defaults(
            func=TestCredentials,
        )

        subparsers.add_parser(
            'test-yaml',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Test YaML file.

            Use this subcommand to check the yaml file.
            """),
            epilog=textwrap.dedent("""
            Examples:

            $ ho test-yaml-file
            $ echo $?
            0

            $ ho --yamlfile bogus test-yaml-file
            $ echo $?
            1

            """),
            help='Test YaML file',
            parents=[TestYaml.get_parser()],
            add_help=False,
        ).set_defaults(
            func=TestYaml,
        )

    def run(self, argv):
        self.args = self.parser.parse_args(argv)

        if self.args.verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        logging.getLogger('handson').setLevel(level)

        self.args.func(self.args).run()

        return True
