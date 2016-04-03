#
# Copyright (c) 2016, SUSE LLC
# All rights reserved.
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
import boto
import boto.ec2
import logging

from handson.region import Region
from handson.subnet import Subnet
# from handson.tag import apply_tag
# from handson.util import read_user_data

log = logging.getLogger(__name__)


class Delegate(Region):

    def __init__(self, args, delegate):
        super(Delegate, self).__init__(args)
        self.args = args
        s = Subnet(self.args, delegate)
        s_obj = s.subnet_obj(create=True, dry_run=self.args.dry_run)
        self._delegate = {
            'delegate': delegate,
            'ec2': None,
            'subnet_obj': s_obj,
        }
        self.ec2()

    def ec2(self):
        """
            fetch ec2 connection, open if necessary
        """
        region = self.region()
        if self._delegate['ec2'] is None:
            log.debug("Connecting to EC2 region {}".format(region))
            self._delegate['ec2'] = boto.ec2.connect_to_region(region)
        assert self._delegate['ec2'] is not None, (
               "Failed to connect to {}".format(region))
        return self._delegate['ec2']
