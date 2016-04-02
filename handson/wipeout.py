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
import handson.myyaml
import logging
import textwrap

from handson.format import CustomFormatter
# from handson.delegate import Delegate
# from handson.region import Region
# from handson.subnet import Subnet
from handson.vpc import VPC

log = logging.getLogger(__name__)


def wipeout_subcommand_parser():
    """
        Necessary for handling -h in, e.g., ho wipeout vpc -h
    """
    parser = argparse.ArgumentParser(
        parents=[],
        conflict_handler='resolve',
    )
    return parser


def wipeout_subcommand_parser_with_retag():
    parser = argparse.ArgumentParser(
        parents=[wipeout_subcommand_parser()],
        conflict_handler='resolve',
    )
    parser.add_argument(
        '-r', '--retag',
        action='store_true', default=None,
        help='retag all objects we touch',
    )
    return parser


class WipeOut(object):

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(
            usage='ho wipeout',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Wipe out (completely delete) AWS entities.

            The documentation for each sub-subcommand can be displayed with

               ho wipeout sub-subcommand --help

            For instance:

               ho wipeout aws --help
               usage: ho wipeout aws [-h]
               ...

            For more information, refer to the README.rst file at
            https://github.com/smithfarm/ceph-auto-aws/README.rst
            """))

        subparsers = parser.add_subparsers(
            title='wipeout subcommands',
            description='valid wipeout subcommands',
            help='wipeout subcommand -h',
        )

        subparsers.add_parser(
            'delegates',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Probe subnets and create them if they are missing.

            This subcommand checks that each delegate has a subnet in AWS VPC,
            in accordance with the 'delegate' stanza of the YaML. If any subnet
            is missing, it is created and the YaML is updated.

            It also checks the Salt Master's dedicated subnet and creates it if
            necessary.

            """),
            epilog=textwrap.dedent(""" Examples:

            $ ho wipeout subnets
            $ echo $?
            0

            """),
            help='Probe subnets and create if missing',
            parents=[wipeout_subcommand_parser_with_retag()],
            add_help=False,
        ).set_defaults(
            func=WipeOutDelegates,
        )

        subparsers.add_parser(
            'vpc',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Wipe out (completely delete) VPC.

            Ipsum dolum

            """),
            epilog=textwrap.dedent(""" Examples:

            $ ho wipeout vpc
            $ echo $?
            0

            """),
            help='Wipe out (completely delete) VPC',
            parents=[wipeout_subcommand_parser_with_retag()],
            add_help=False,
        ).set_defaults(
            func=WipeOutVPC,
        )

        return parser


class InitArgs(object):

    def __init__(self, args):
        handson.myyaml._yfn = args.yamlfile


class WipeOutDelegates(InitArgs):

    def __init__(self, args):
        super(WipeOutDelegates, self).__init__(args)
        self.args = args

    def run(self):
        pass


class WipeOutVPC(InitArgs):

    def __init__(self, args):
        super(WipeOutVPC, self).__init__(args)
        self.args = args

    def run(self):
        VPC(self.args).wipeout()
