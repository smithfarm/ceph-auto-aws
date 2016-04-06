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
    ClusterOptions,
)
from handson.delegate import Delegate
from handson.misc import (
    CustomFormatter,
    InitArgs,
)
from handson.parsers import (
    cluster_options_parser,
)

log = logging.getLogger(__name__)


class Stop(object):

    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(
            usage='ho stop',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Stop AWS delegates.

            The documentation for each sub-subcommand can be displayed with

               ho stop sub-subcommand --help

            For instance:

               ho stop delegates --help
               usage: ho stop delegates [-h]
               ...

            For more information, refer to the README.rst file at
            https://github.com/smithfarm/ceph-auto-aws/README.rst
            """))

        subparsers = parser.add_subparsers(
            title='stop subcommands',
            description='valid stop subcommands',
            help='stop subcommand -h',
        )

        subparsers.add_parser(
            'delegates',
            formatter_class=CustomFormatter,
            description=textwrap.dedent("""\
            Stop (suspend) delegate clusters.

            """),
            epilog=textwrap.dedent(""" Examples:

            $ ho stop subnets
            $ echo $?
            0

            """),
            help='Stop (suspend) delegate clusters',
            parents=[cluster_options_parser()],
            add_help=False,
        ).set_defaults(
            func=StopDelegates,
        )

        return parser


class StopDelegates(InitArgs, ClusterOptions):

    def __init__(self, args):
        super(StopDelegates, self).__init__(args)
        self.args = args

    def run(self):
        self.process_delegate_list()
        for d in self.args.delegate_list:
            log.info("Stopping cluster for delegate {}".format(d))
            d = Delegate(self.args, d)
            d.stop(dry_run=self.args.dry_run)
