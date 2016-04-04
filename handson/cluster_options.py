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

from handson.misc import error_exit, subcommand_parser
from handson.myyaml import stanza

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
            # ti = map(int, t)  # <- SEGFAULT
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
            parents=[subcommand_parser()],
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


def dry_run_only_parser():
        parser = argparse.ArgumentParser(
            description="Cluster",
            parents=[subcommand_parser()],
            add_help=False,
        )

        parser.add_argument(
            '-d', '--dry-run',
            action='store_true', default=None,
            help="Go through the motions, but do nothing",
        )

        return parser


class ClusterOptions(object):

    def validate_delegate_list(self):
        dl = self.args.delegate_list
        if dl is None or len(dl) == 0:
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
        if dl[-1] > max_delegates:
            error_exit(("Delegate list exceeds {!r} (maximum number of " +
                        "delegates in yaml)").format(max_delegates))

    def process_delegate_list(self):
        max_d = stanza('delegates')
        if self.args.delegate_list is None:
            self.args.delegate_list = []
        if self.args.all:
            self.args.delegate_list = range(1, max_d + 1)
        if self.args.master:
            self.args.delegate_list.insert(0, 0)
        self.validate_delegate_list()
        log.info("Delegate list is {!r}".format(self.args.delegate_list))
