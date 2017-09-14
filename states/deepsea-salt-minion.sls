# deepsea-salt-minion.sls
#
# Apply this state on the Delegate minion nodes (all nodes except the Root
# Master), but only after applying the "deepsea-salt-master" state on the local
# master nodes.

salt-minion-installed:
  pkg.installed:
    - pkgs:
      - salt-minion

# point the local minions to their new local master
switch-master:
  cmd.script:
    - name: salt://switch-master.sh
    - cwd: /etc
    - user: root

restart-salt-minion-service:
  cmd.run:
    - name: systemctl restart salt-minion.service
    - user: root

