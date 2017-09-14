#!/bin/bash
#
# resiliency-data.sh
#
# Prime cluster with data (for Resiliency lab)
#
dd if=/dev/zero of=/tmp/foo bs=4K count=1K # 4M file
for i in {1..400}
do  
    rados -p rbd put lb$i /tmp/foo
done
rm  /tmp/foo
