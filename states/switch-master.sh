#!/bin/sh
LOCAL_MASTER=$(cat /etc/susecon2017/local_master)
sed -i "s/^master.*\$/master: $LOCAL_MASTER/" /etc/salt/minion.d/ceph.conf
rm -f /etc/salt/pki/minion/minion_master.pub
