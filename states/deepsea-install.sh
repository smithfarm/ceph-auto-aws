#!/bin/bash -x
#
# install DeepSea on local master (will be run as root)
#

#---------------------------------------------------------
#--- can be dropped once python-click reaches SES5 channel
#---------------------------------------------------------
sudo zypper --non-interactive --no-gpg-checks addrepo http://download.opensuse.org/repositories/devel:/languages:/python/SLE_12_SP3/devel:languages:python.repo
sudo zypper --non-interactive --no-gpg-checks refresh
sudo zypper --non-interactive --no-gpg-checks install --no-recommends python-click
sudo zypper --non-interactive --no-gpg-checks removerepo devel_languages_python
#---------------------------------------------------------
#--- can be dropped once python-click reaches SES5 channel
#---------------------------------------------------------

sudo zypper --non-interactive --no-gpg-checks install --no-recommends make rpm
test -d DeepSea || git clone --depth 1 --branch susecon2017 https://github.com/smithfarm/DeepSea.git
cd DeepSea
ls -l
sudo make install
sudo zypper --non-interactive install --no-recommends $(rpmspec --requires -q -v deepsea.spec | grep manual | awk '{print $2}')
