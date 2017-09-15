#!/bin/bash
# 
# Possibly arrange for ssh to the Delegate Nodes to be non-interactive

for n in 10 11 12 13 14 15 16 17 18 19 ; do
    ssh-keygen -R 10.0.{{ grains['delegate'] }}.$n || :
done

for n in 10 11 12 13 14 15 16 17 18 19 ; do
    ssh -o StrictHostKeyChecking=no cephadm@10.0.{{ grains['delegate'] }}.$n echo || :
done

for n in 10 11 12 13 14 15 16 17 18 19 ; do
    ssh-keygen -R ip-10-0-{{ grains['delegate'] }}-$n || :
done

for n in 10 11 12 13 14 15 16 17 18 19 ; do
    ssh -o StrictHostKeyChecking=no cephadm@ip-10-0-{{ grains['delegate'] }}-$n echo || :
done
