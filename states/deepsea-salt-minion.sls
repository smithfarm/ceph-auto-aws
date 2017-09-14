# deepsea-salt-minion.sls
#
# apply this state on the delegate (DeepSea) minion nodes
# (i.e. all the delegate nodes)

salt:
  pkg.installed:
    - pkgs:
      - salt-minion

switch-master:
  cmd.script:
    - name: salt://switch-master.sh
    - cwd: /etc
    - user: root

mycommand2:
  cmd.run:
    - name: systemctl restart salt-minion.service
    - user: root

