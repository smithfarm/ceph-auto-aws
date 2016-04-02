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

from handson.error import error_exit
from handson.format import CustomFormatter

log = logging.getLogger(__name__)


def expand_delegate_list(raw_input):
    """
        Given a string, raw_input, that looks like "1-3,7"
        return a sorted list of integers [1, 2, 3, 7]
    """
    if raw_input is None:
        return None
    intermediate_list = []
    for item in raw_input.split(','):
        t = item.split('-')
        try:
            ti = list(map(int, t))
            # ti = map(int, t) <- SEGFAULT
        except ValueError as e:
            error_exit(e)
        if len(ti) == 1:
            intermediate_list.extend(ti)
            continue
        if len(ti) == 2:
            if (
                    ti[1] > ti[0] and
                    (ti[1] - ti[0]) < 50
            ):
                intermediate_list.extend(range(ti[0], ti[1]+1))
                continue
        error_exit("Illegal delegate list")
    final_list = list(sorted(set(intermediate_list), key=int))
    if final_list[0] < 1:
        error_exit("detected too-low delegate (min. 1)")
    if final_list[-1] > 50:
        error_exit("detected too-high delegate (max. 50)")
    return final_list


class ParseDelegateList(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, expand_delegate_list(values))


def cluster_options_parser():
        parser = argparse.ArgumentParser(
            description="Cluster",
            add_help=False,
        )

        parser.add_argument(
            '-a', '--all',
            action='store_true',
            help="Apply subcommand to all delegate clusters",
        )

        parser.add_argument(
            '-d', '--dry-run',
            action='store_true', default=None,
            help="Go through the motions, but do nothing",
        )

        parser.add_argument(
            '-m', '--master',
            action='store_true', default=None,
            help="Apply subcommand to Salt Master",
        )

        parser.add_argument(
            'delegate_list', nargs='?', default=None,
            action=ParseDelegateList,
            help="e.g. 1-3,5",
        )

        return parser


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

        return parser


class InitArgs(object):

    def __init__(self, args):
        handson.myyaml._yfn = args.yamlfile


class InstallDelegate(InitArgs):

    def __init__(self, args):
        super(InstallDelegate, self).__init__(args)
        self.args = args

    def report_options(self):
        dr = "ON" if self.args.dry_run else "OFF"
        log.debug("Dry run is {}".format(dr))
        log.info("Delegate list is {!r}".format(self.args.delegate_list))

    def validate_delegate_list(self):
        if self.args.delegate_list is None:
            return True
        max_delegates = handson.myyaml.stanza('delegates')
        log.debug("Maximum number of delegates is {!r}".format(max_delegates))
        if (
                max_delegates is None or
                max_delegates < 1 or
                max_delegates > 50
        ):  # pragma: no cover
            error_exit("Bad number of delegates in yaml: {!r}".
                       format(max_delegates))
        if self.args.delegate_list[-1] > max_delegates:
            error_exit(("Delegate list exceeds {!r} (maximum number of " +
                        "delegates in yaml)").format(max_delegates))

    def run(self):
        self.report_options()
        self.validate_delegate_list()
