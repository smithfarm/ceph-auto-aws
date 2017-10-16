#!/bin/bash -x
#
# Script used by deepsea-salt-master.sls to install DeepSea on Delegate (local)
# master node

# install DeepSea from RPM
sudo zypper --non-interactive --no-gpg-checks addrepo http://download.opensuse.org/repositories/filesystems:ceph/SLE_12_SP3/filesystems:ceph.repo
sudo zypper --non-interactive --no-gpg-checks refresh
sudo zypper --non-interactive --no-gpg-checks install --no-recommends deepsea deepsea-qa
sudo zypper --non-interactive --no-gpg-checks removerepo filesystems_ceph

# install DeepSea from source
#sudo zypper --non-interactive --no-gpg-checks install --no-recommends make rpm
#test -d DeepSea || git clone --depth 1 --branch susecon2017 https://github.com/smithfarm/DeepSea.git
#cd DeepSea
#ls -l
#sudo make install
#sudo zypper --non-interactive install --no-recommends $(rpmspec --requires -q -v deepsea.spec | grep manual | awk '{print $2}')
