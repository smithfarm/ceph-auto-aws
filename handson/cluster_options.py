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

import logging

from handson.myyaml import stanza

log = logging.getLogger(__name__)


class ClusterOptions(object):

    def validate_delegate_list(self):
        dl = self.args.delegate_list
        if dl is None or len(dl) == 0:
            return True
        max_delegates = stanza('delegates')
        log.debug("Maximum number of delegates is {!r}".format(max_delegates))
        assert (
                max_delegates is not None and
                max_delegates > 0 and
                max_delegates <= 100
        ), "Bad delegates stanza in YAML: {!r}".format(max_delegates)
        assert dl[-1] <= max_delegates, (
            ("Delegate list exceeds {!r} (maximum number of " +
             "delegates in YAML)").format(max_delegates)
        )

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
