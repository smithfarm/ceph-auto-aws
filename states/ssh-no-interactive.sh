#!/bin/bash
ssh-keygen -R 10.0.{{ grains['delegate'] }}.10 || :
ssh-keygen -R 10.0.{{ grains['delegate'] }}.11 || :
ssh-keygen -R 10.0.{{ grains['delegate'] }}.12 || :
ssh-keygen -R 10.0.{{ grains['delegate'] }}.13 || :
ssh-keygen -R 10.0.{{ grains['delegate'] }}.14 || :
ssh -o StrictHostKeyChecking=no cephadm@10.0.{{ grains['delegate'] }}.10 echo || :
ssh -o StrictHostKeyChecking=no cephadm@10.0.{{ grains['delegate'] }}.11 echo || :
ssh -o StrictHostKeyChecking=no cephadm@10.0.{{ grains['delegate'] }}.12 echo || :
ssh -o StrictHostKeyChecking=no cephadm@10.0.{{ grains['delegate'] }}.13 echo || :
ssh -o StrictHostKeyChecking=no cephadm@10.0.{{ grains['delegate'] }}.14 echo || :
ssh-keygen -R ip-10-0-{{ grains['delegate'] }}-10 || :
ssh-keygen -R ip-10-0-{{ grains['delegate'] }}-11 || :
ssh-keygen -R ip-10-0-{{ grains['delegate'] }}-12 || :
ssh-keygen -R ip-10-0-{{ grains['delegate'] }}-13 || :
ssh-keygen -R ip-10-0-{{ grains['delegate'] }}-14 || :
ssh -o StrictHostKeyChecking=no cephadm@ip-10-0-{{ grains['delegate'] }}-10 echo || :
ssh -o StrictHostKeyChecking=no cephadm@ip-10-0-{{ grains['delegate'] }}-11 echo || :
ssh -o StrictHostKeyChecking=no cephadm@ip-10-0-{{ grains['delegate'] }}-12 echo || :
ssh -o StrictHostKeyChecking=no cephadm@ip-10-0-{{ grains['delegate'] }}-13 echo || :
ssh -o StrictHostKeyChecking=no cephadm@ip-10-0-{{ grains['delegate'] }}-14 echo || :
