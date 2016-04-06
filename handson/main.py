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

import handson.myyaml
import logging
import sys
import textwrap

from argparse import ArgumentParser
from handson.install import Install
from handson.misc import CustomFormatter
from handson.probe import Probe
from handson.start import Start
from handson.stop import Stop
from handson.wipeout import WipeOut

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

__version__ = "0.1.5"


class HandsOn(object):

    def __init__(self):
        self.parser = ArgumentParser(
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Scripting for hands-on demonstrations of Ceph.

            The documentation for each subcommand can be displayed with

               ho subcommand --help

            For instance:

               ho install --help
               usage: ho install [-h]
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
            help='specify yaml file to read',
        )

        subparsers = self.parser.add_subparsers(
            title='subcommands',
            description='valid subcommands',
            help='subcommand -h',
        )

        subparsers.add_parser(
            'install',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Create Ceph clusters in AWS.

            Creates Ceph clusters in AWS according to the yaml configuration.
            """),
            epilog=textwrap.dedent("""
            Examples:

            $ ho install

            """),
            help='Create Ceph clusters in AWS',
            parents=[Install.get_parser()],
            add_help=False,
        )

        subparsers.add_parser(
            'probe',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Probe AWS connection and cluster configuration.
            """),
            epilog=textwrap.dedent("""
            Examples:

            $ ho probe yaml

            """),
            help='Probe AWS connection and cluster configuration',
            parents=[Probe.get_parser()],
            add_help=False,
        )

        subparsers.add_parser(
            'start',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Start (revive) stopped Delegate Clusters
            """),
            epilog=textwrap.dedent("""
            Examples:

            $ ho start delegate 1

            """),
            help='Start (revive) stopped Delegate Clusters',
            parents=[Start.get_parser()],
            add_help=False,
        )

        subparsers.add_parser(
            'stop',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Stop (suspend) Delegate Clusters
            """),
            epilog=textwrap.dedent("""
            Examples:

            $ ho stop delegate 1

            """),
            help='Stop (suspend) Delegate Clusters',
            parents=[Stop.get_parser()],
            add_help=False,
        )

        subparsers.add_parser(
            'wipeout',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Wipe out (completely remove) AWS entities.
            """),
            epilog=textwrap.dedent("""
            Examples:

            $ ho wipeout vpc

            """),
            help='Wipe out (completely remove) AWS entities',
            parents=[WipeOut.get_parser()],
            add_help=False,
        )

    def run(self, argv):
        self.args = self.parser.parse_args(argv)

        if self.args.verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        logging.getLogger('handson').setLevel(level)

        # log.info("HandsOn self.args {!r}".format(self.args))
        handson.myyaml.initialize_internal_buffers()
        self.args.func(self.args).run()

        sys.exit(0)
