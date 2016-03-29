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
import pyaml
import yaml

from handson.aws import AWS
from handson.error import error_exit

log = logging.getLogger(__name__)

tree_stanzas = [
    'cluster-definition',
    'delegates',
    'keyname',
    'region',
    'role-definitions',
    'subnets',
    'types',
    'vpc',
]

role_definition_keys = [
    'ami-id',
    'instance',
    'replace-from-environment',
    'type',
    'user-data',
    'volume',
]


class MyYaml(AWS):

    def __init__(self, args):
        super(AWS, self).__init__(args)

    def yaml_file_name(self, fn=None):
        if 'yaml_file_name' not in self._yaml:
            self._yaml['yaml_file_name'] = fn
        return self._yaml['yaml_file_name']

    def tree(self):
        # log.debug("{!r}".format(self._yaml))
        if 'tree' not in self._yaml:
            self.load()
            tree = self._yaml['tree']
            if type(tree) is not dict:  # pragma: no cover
                error_exit("yaml file is totally munged")
            for stanza in tree_stanzas:
                if stanza not in tree_stanzas:  # pragma: no cover
                    error_exit("{!r} stanza missing in yaml file"
                               .format(stanza))
        return self._yaml['tree']

    def write(self):  # pragma: no cover
        fn = self.yaml_file_name()
        tree = self.tree()
        with open(fn, 'w') as outfile:
            outfile.write(
                pyaml.dump(tree, vspacing=[1, 0])
            )

    def load(self, yaml_file=None):
        if yaml_file is None:
            yaml_file = self.yaml_file_name()
        log.debug("yaml_file is {!r}".format(yaml_file))
        f = open(yaml_file)
        self._yaml['tree'] = yaml.safe_load(f)
        f.close()
        log.info("Loaded yaml from {}".format(yaml_file))

    def validate_role_definitions(self):  # pragma: no cover
        tree = self.tree()
        types = tree['types']
        stanza = tree['role-definitions']
        if type(stanza) is not dict:
            error_exit("role-definitions stanza is not a mapping")
        roles = []
        for role in stanza:
            log.debug("Detected definition stanza of role {!r}".format(role))
            roles.append(role)
            role_def = stanza[role]
            if role_def is None:
                continue
            if type(role_def) is not dict:
                error_exit("Role definition {!r} is not a mapping"
                           .format(role))
            for key in role_def:
                log.debug("Considering role definition {!r}".format(role_def))
                log.debug("Considering whether key {!r} is in {!r}"
                          .format(key, role_definition_keys))
                if key not in role_definition_keys:
                    error_exit(
                        "Role definition {!r} contains illegal attribute {!r}"
                        .format(role, key)
                    )
                val = role_def[key]
                if key == 'type' and val not in types:
                    error_exit(
                        "Illegal type {!r} detected in role definition {!r}"
                        .format(val, role)
                    )
                keys.append(key)
        log.info("Detected roles {!r}".format(roles))
        return roles

    def role_exists(self, role):
        tree = self.tree()
        stanza = tree['role-definitions']
        return True if role in stanza else False

    def validate_cluster_definition(self):  # pragma: no cover
        tree = self.tree()
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
