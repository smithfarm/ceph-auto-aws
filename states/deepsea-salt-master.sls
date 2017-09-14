# deepsea-salt-master.sls
#
# apply this state on the delegate (DeepSea) master nodes

salt-master-install:
  pkg.installed:
    - pkgs:
      - salt-master

deepsea-install:
  cmd.script:
    - name: salt://deepsea-install.sh
    - cwd: /home/cephadm
    - user: cephadm

restart-salt-master:
  cmd.run:
    - name: systemctl start salt-master.service
    - user: root

/home/cephadm/bin/health-ok:
  file.managed:
    - source: salt://health-ok.sh
    - user: cephadm
    - group: users
    - mode: 755
