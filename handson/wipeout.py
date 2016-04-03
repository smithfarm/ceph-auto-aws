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

from handson.cluster_options import (
    cluster_options_parser,
    dry_run_only_parser,
    ClusterOptions,
)
from handson.delegate import Delegate
from handson.misc import (
    CustomFormatter,
)
# from handson.region import Region
from handson.subnet import Subnet
from handson.vpc import VPC

log = logging.getLogger(__name__)


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

               ho wipeout delegates --help
               usage: ho wipeout delegates [-h]
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
            Wipe out (completely delete) delegate clusters.

            """),
            epilog=textwrap.dedent(""" Examples:

            $ ho wipeout subnets
            $ echo $?
            0

            """),
            help='Wipe out (completely delete) delegate clusters',
            parents=[cluster_options_parser()],
            add_help=False,
        ).set_defaults(
            func=WipeOutDelegates,
        )

        subparsers.add_parser(
            'subnets',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Wipe out (completely delete) one or more subnets.

            Ipsum dolum

            """),
            epilog=textwrap.dedent(""" Examples:

            $ ho wipeout subnets 3
            $ ho wipeout subnets 1,5
            $ ho wipeout subnets 1-3,6

            """),
            help='Wipe out (completely delete) one or more subnets',
            parents=[cluster_options_parser()],
            add_help=False,
        ).set_defaults(
            func=WipeOutSubnets,
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
            parents=[dry_run_only_parser()],
            add_help=False,
        ).set_defaults(
            func=WipeOutVPC,
        )

        return parser


class InitArgs(object):

    def __init__(self, args):
        handson.myyaml._yfn = args.yamlfile


class WipeOutDelegates(InitArgs, ClusterOptions):

    def __init__(self, args):
        super(WipeOutDelegates, self).__init__(args)
        self.args = args

    def run(self):
        self.process_delegate_list()
        for d in self.args.delegate_list:
            log.info("Wiping out cluster for delegate {}".format(d))
            d = Delegate(self.args, d)
            d.wipeout(dry_run=self.args.dry_run)


class WipeOutSubnets(InitArgs, ClusterOptions):

    def __init__(self, args):
        super(WipeOutSubnets, self).__init__(args)
        self.args = args

    def run(self):
        self.process_delegate_list()
        for d in self.args.delegate_list:
            s = Subnet(self.args, d)
            s_obj = s.subnet_obj(create=False)
            if s_obj:
                s.wipeout(dry_run=self.args.dry_run)


class WipeOutVPC(InitArgs):

    def __init__(self, args):
        super(WipeOutVPC, self).__init__(args)
        self.args = args

    def run(self):
        v = VPC(self.args)
        v.vpc_obj(create=False)
        v.wipeout(dry_run=self.args.dry_run)
