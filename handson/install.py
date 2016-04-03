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

from handson.cluster_options import (
    cluster_options_parser,
    ClusterOptions,
    dry_run_only_parser,
)
from handson.misc import (
    CustomFormatter,
    InitArgs,
    subcommand_parser_with_retag,
)
from handson.myyaml import stanza
from handson.subnet import Subnet
from handson.vpc import VPC

log = logging.getLogger(__name__)


class Install(object):

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(
            usage='ho install',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Install delegats.

            The documentation for each sub-subcommand can be displayed with

               ho install sub-subcommand --help

            For instance:

               ho install delegate --help
               usage: ho install delegate [-h]
               ...

            For more information, refer to the README.rst file at
            https://github.com/smithfarm/ceph-auto-aws/README.rst
            """))

        subparsers = parser.add_subparsers(
            title='install subcommands',
            description='valid install subcommands',
            help='install subcommand -h',
        )

        subparsers.add_parser(
            'delegates',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Install delegate cluster(s) in AWS.

            """),
            epilog=textwrap.dedent("""
            Example:

            $ ho install delegates 1-12
            $ echo $?
            0

            """),
            help='Install delegate cluster(s) in AWS',
            parents=[cluster_options_parser()],
            add_help=False,
        ).set_defaults(
            func=InstallDelegate,
        )

        subparsers.add_parser(
            'subnets',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Install delegate subnet(s) in AWS.

            """),
            epilog=textwrap.dedent("""
            Example:

            $ ho install subnets 1-12
            $ ho install subnets --all
            $ ho install subnets --all --dry-run

            """),
            help='Install delegate subnet(s) in AWS',
            parents=[cluster_options_parser()],
            add_help=False,
        ).set_defaults(
            func=InstallSubnets,
        )

        subparsers.add_parser(
            'vpc',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Install Virtual Private Cloud (VPC).

            """),
            epilog=textwrap.dedent("""
            Example:

            $ ho install vpc
            $ ho install --dry-run

            """),
            help='Install Virtual Private Cloud (VPC)',
            parents=[dry_run_only_parser()],
            add_help=False,
        ).set_defaults(
            func=InstallVPC,
        )

        return parser


class InstallDelegate(InitArgs, ClusterOptions):

    def __init__(self, args):
        super(InstallDelegate, self).__init__(args)
        self.args = args

    def run(self):
        self.process_delegate_list()
        if self.args.dry_run:
            return None


class InstallSubnets(InitArgs, ClusterOptions):

    def __init__(self, args):
        super(InstallSubnets, self).__init__(args)
        self.args = args

    def run(self):
        max_d = stanza('delegates')
        if self.args.delegate_list is None:
            self.args.delegate_list = []
        if self.args.all:
            self.args.delegate_list = range(1, max_d + 1)
        if self.args.master:
            self.args.delegate_list.insert(0, 0)
        self.process_delegate_list()
        for d in self.args.delegate_list:
            log.info("Installing subnet for delegate {}".format(d))
            if self.args.dry_run:
                log.info("Dry run: doing nothing")
                continue
            c = Subnet(self.args, d)
            c.subnet_obj(create=True)


class InstallVPC(InitArgs):

    def __init__(self, args):
        super(InstallVPC, self).__init__(args)
        self.args = args

    def run(self):
        log.info("Probing VPC")
        vpc_obj = VPC(self.args).vpc_obj(create=False)
        if vpc_obj.id:
            log.info("VPC already installed")
            return None
        log.info("Creating VPC")
        if self.args.dry_run:
            log.info("Dry run: do nothing")
            return None
        vpc_obj = VPC(self.args).vpc_obj(create=True)
