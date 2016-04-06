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
import re

log = logging.getLogger(__name__)


def get_file_as_string(fn):
    """
        Given a filename, returns the file's contents in a string.
    """
    r = ''
    with open(fn) as fh:
        r = fh.read()
        fh.close()
    return r


def derive_ip_address(cidr_block, delegate, final8):
    """
        Given a CIDR block string, a delegate number, and an integer
        representing the final 8 bits of the IP address, construct and return
        the IP address derived from this values.  For example, if cidr_block is
        10.0.0.0/16, the delegate number is 10, and the final8 is 8, the
        derived IP address will be 10.0.10.8.
    """
    match = re.match(r'\d+\.\d+', cidr_block)
    assert match, (
        "{} passed to derive_ip_address() is not a CIDR block!"
        .format(cidr_block)
    )
    result = '{}.{}.{}'.format(match.group(0), delegate, final8)
    return result


def template_token_subst(buf, key, val):
    """
        Given a string (buf), a key (e.g. '@@MASTER_IP@@') and val, replace all
        occurrences of key in buf with val. Return the new string.
    """
    targetre = re.compile(re.escape(key))
    return re.sub(targetre, str(val), buf)
