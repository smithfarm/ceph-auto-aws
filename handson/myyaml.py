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
import yaml
import pyaml


class MyYaml(object):

    def __init__(self, yamlfile):
        self._yaml = {}
        self.yaml_file_name(yamlfile)

    def yaml_file_name(self, fn=None):
        if 'yaml_file_name' not in self._yaml:
            self._yaml['yaml_file_name'] = fn
        return self._yaml['yaml_file_name']

    def tree(self):
        print "{!r}".format(self._yaml)
        if 'tree' not in self._yaml:
            self.load()
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
        print "yaml_file is {!r}".format(yaml_file)
        f = open(yaml_file)
        self._yaml['tree'] = yaml.safe_load(f)
        f.close()
