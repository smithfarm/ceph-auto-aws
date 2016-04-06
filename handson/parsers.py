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


def subcommand_parser():
    """
        Necessary for handling -h in, e.g., ho probe aws -h
    """
    parser = argparse.ArgumentParser(
        parents=[],
        conflict_handler='resolve',
    )
    return parser


def subcommand_parser_with_retag():
    parser = argparse.ArgumentParser(
        parents=[subcommand_parser()],
        conflict_handler='resolve',
    )
    parser.add_argument(
        '-r', '--retag',
        action='store_true', default=None,
        help='retag all objects we touch',
    )
    return parser


def expand_delegate_list(raw_input):
    """
        Given a string raw_input, that looks like "1-3,7"
        return a sorted list of integers [1, 2, 3, 7]
    """
    if raw_input is None:
        return None
    intermediate_list = []
    for item in raw_input.split(','):
        t = item.split('-')
        try:
            ti = list(map(int, t))
            # ti = map(int, t)  # <- SEGFAULT IN PYTHON 3.4.1
        except ValueError as e:
            raise e
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
        assert 1 == 0, "Illegal delegate list {!r}".format(ti)
    final_list = list(sorted(set(intermediate_list), key=int))
    assert final_list[0] > 0, "detected too-low delegate (min. 1)"
    assert final_list[-1] <= 50, "detected too-high delegate (max. 50)"
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
