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
import logging

from handson.myyaml import stanza
from handson.region import Region
from handson.util import get_file_as_string

log = logging.getLogger(__name__)


class Keypair(Region):

    def __init__(self, args, delegate):
        super(Keypair, self).__init__(args)
        self.args = args
        self._keypair = {
            'delegate': delegate,
            'keypair_obj': None,
            'keyname': None,
        }

    def get_keyname_from_yaml(self):
        if self._keypair['keyname']:
            return self._keypair['keyname']
        k_stanza = stanza('keypairs')
        log.debug("Keypairs stanza is {!r}".format(k_stanza))
        assert type(k_stanza) == dict
        d = self._keypair['delegate']
        if d in k_stanza:
            if 'keyname' in k_stanza[d]:
                if k_stanza[d]['keyname']:
                    self._keypair['keyname'] = k_stanza[d]['keyname']
                    return k_stanza[d]['keyname']
        return None

    def get_key_material(self, keyname):
        fn = "keys/{}.pub".format(keyname)
        return get_file_as_string(fn)

    def get_keypair_from_aws(self):
        keyname_from_yaml = self.get_keyname_from_yaml()
        if keyname_from_yaml:
            log.debug("Getting keypair {} from AWS".format(keyname_from_yaml))
            k_list = self.ec2().get_all_key_pairs(keynames=[keyname_from_yaml])
            log.info("Keypair object {} fetched from AWS".
                     format(keyname_from_yaml))
            self._keypair['keypair_obj'] = k_list[0]
            return True
        return False

    def import_keypair(self, dry_run):
        d = self._keypair['delegate']
        if dry_run:
            log.info("Dry run: doing nothing")
            return None
        # we pitifully assume the user has already run generate-keys.sh
        k_name = "{}-d{}".format(stanza('keyname'), d)
        k_mat = self.get_key_material(k_name)
        k_obj = self.ec2().import_key_pair(k_name, k_mat)
        log.info("Keypair {} imported to AWS".format(k_name))
        self._keypair['keypair_obj'] = k_obj
        self._keypair['key_name'] = k_name
        k_stanza = stanza('keypairs')
        k_stanza[d] = {}
        k_stanza[d]['keyname'] = k_name
        stanza('keypairs', k_stanza)

    def keypair_obj(self, import_ok=False, dry_run=False):
        if self._keypair['keypair_obj'] is not None:
            return self._keypair['keypair_obj']
        d = self._keypair['delegate']
        if self.get_keypair_from_aws():
            return self._keypair['keypair_obj']
        log.info("Delegate {} keypair not imported yet: importing".format(d))
        assert import_ok, (
           "Delegate {} keypair should be imported, but import not allowed"
           .format(d)
        )
        k_obj = self.import_keypair(dry_run)
        return k_obj

    def wipeout(self, dry_run=False):
        k_name = self.get_keyname_from_yaml(self)
        if k_name:
            # wipeout
            pass
        log.info("Delegate {} has no keypair in YAML: doing nothing"
                 .format(self._keypair['delegate']))
