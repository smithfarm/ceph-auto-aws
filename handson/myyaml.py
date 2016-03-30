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
import os

from handson.error import error_exit
from yaml import safe_load
from pyaml import dump

log = logging.getLogger(__name__)

tree_stanzas = {
    'cluster-definition': {'default': [{'role': 'admin'}], 'type': list},
    'delegates': {'default': 1, 'type': int},
    'keyname': {'default': '', 'type': str},
    'region': {'default': 'eu-west-1', 'type': str},
    'role-definitions': {'default': {
        'admin': None,
        'defaults': {
            'ami-id': '',
            'replace-from-environment': [],
            'type': 't2.small',
            'user-data': ''
        },
        'master': None,
        'mon': None,
        'osd': None,
        'windows': None
    }, 'type': dict},
    'subnets': {'default': [], 'type': list},
    'types': {'default': ['t2.small'], 'type': list},
    'vpc': {'default': [], 'type': list}
}

role_definition_keys = [
    'ami-id',
    'replace-from-environment',
    'type',
    'user-data',
    'volume',
]

_cache = {}
_cache_populated = False
_yfn = None


def tree():
    # log.debug("{!r}".format(self._yaml))
    global _cache
    if _cache is None:
        _cache = load()
        if type(_cache) is not dict:  # pragma: no cover
            error_exit("yaml file is totally munged")
        for stanza in tree_stanzas:
            if stanza not in _cache:  # pragma: no cover
                error_exit("{!r} stanza missing in yaml file"
                           .format(stanza))
    return _cache


def yaml_file_name(fn=None):
    global _yfn
    if _yfn is None and fn is None:
        error_exit("YAML file name not initialized")
    if fn is None:
        return _yfn
    _yfn = fn
    return _yfn


def touch(fname, times=None):
    with open(fname, 'a'):
            os.utime(fname, times)


def load():
    """
        Load yaml tree into cache from yaml file
    """
    global _cache, _cache_populated
    if _cache_populated:
        log.debug("YAML cache already populated")
        return None
    yfn = yaml_file_name()
    log.debug("Loading YAML file {!r}".format(yfn))
    touch(yfn)
    with open(yfn) as f:
        _cache = safe_load(f)
    _cache_populated = True
    log.info("Loaded yaml tree from {!r}".format(yfn))
    return None


def write():  # pragma: no cover
    global _cache
    yfn = yaml_file_name()
    touch(yfn)
    with open(yfn, 'w') as outfile:
        outfile.write(dump(_cache, vspacing=[1, 0]))
    return None


def stanza_is_present(s):
    global _cache
    if s not in _cache:
        error_exit("No stanza {!r} in YAML file".format(s))


def apply_default(k):
    global _cache
    if _cache is None:
        _cache = {}
    if k not in _cache or _cache[k] is None:
        _cache[k] = tree_stanzas[k]['default']
        write()
    return None


def check_if_malformed(k):
    global _cache
    t = tree_stanzas[k]['type']
    if type(_cache[k]) is not t:
        log.fatal("Malformed YAML stanza {!r} is not {!r}".format(k, t))
        assert 1 == 0


def stanza_is_sane(k):
    apply_default(k)
    check_if_malformed(k)


def stanza(k):
    global _cache
    load()
    stanza_is_sane(k)
    return _cache[k]


def probe_yaml():
    load()
    for key in tree_stanzas:
        stanza_is_sane(key)


def role_def_valid(role, rd):
    if type(rd) is not dict:
        error_exit("Role definition {!r} is not a mapping"
                   .format(role))
    for key in rd:
        log.debug("Considering attribute {!r}".format(key))
        if key not in role_definition_keys:
            error_exit(
                "Role definition {!r} contains illegal attribute {!r}"
                .format(role, key)
            )
        val = role_def[key]
        if key == 'type' and val not in stanza('type'):
            error_exit(
                "Illegal type {!r} detected in role definition {!r}"
                .format(val, role)
            )


def validate_role_definitions():  # pragma: no cover
    types = stanza('types')
    rd = stanza('role-definitions')
    if type(rd) is not dict:
        error_exit("role-definitions stanza is not a mapping")
    roles = []
    for role in rd:
        log.debug("Detected definition stanza of role {!r}".format(role))
        roles.append(role)
        role_def = rd[role]
        if role_def is None:
            continue
        assert role_def_valid(role, role_def)
    log.info("Detected roles {!r}".format(roles))
    return roles


def role_exists(role):
    stanza = tree['role-definitions']
    return True if role in stanza else False


def validate_cluster_definition():  # pragma: no cover
    cluster_def = tree['cluster-definition']
    if cluster_def is None:
        error_exit("cluster-definition stanza is empty")
    if type(cluster_def) is not list:
        error_exit("cluster-definition is not a sequence")
    if len(cluster_def) < 1:
        error_exit("cluster-definition stanza is empty")
    log.info("Detected cluster-definition stanza")
    roles = []
    for instance_def in cluster_def:
        log.debug("Considering instance definition {!r}"
                  .format(instance_def))
        if type(instance_def) is not dict:
            error_exit("Instance definition is not a mapping")
        if len(instance_def.items()) < 0:
            error_exit("Instance definition is empty")
        if len(instance_def.items()) > 1:
            error_exit("Instance definition contains more than one "
                       "attribute")
        log.debug("Instance definition {!r}".format(instance_def.items()))
        key = instance_def.items()[0][0]
        if key != 'role':
            error_exit("Instance definition key is not 'role'")
        val = instance_def[key]
        if val is None:
            error_exit("Detected empty 'role' attribute in cluster "
                       "definition")
        if type(val) is not str:
            error_exit("Detected non-string 'role' attribute in cluster "
                       "definition")
        if val in roles:
            error_exit("Detected duplicate role {!r} in cluster definition"
                       .format(val))
        log.info("Detected role {!r} in cluster definition".format(val))
        if val.lower() == "defaults":
            error_exit("Detected bogus role {!r} in cluster definition"
                       .format(val))
        roles.append(val)
        if not self.role_exists(val):
            error_exit("Role {!r} is undefined".format(val))
    return True
