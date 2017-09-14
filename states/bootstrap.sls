# bootstrap.sls
#
# apply this state on all delegate minions (i.e. all delegate instances)

mycommand2:
  cmd.run:
    - name: zypper --gpg-auto-import-keys ref
    - user: root

salt:
  pkg.installed:
    - pkgs:
      - salt-minion
  user.present:
    - name: cephadm
    - password: ceDx/cy5D.nug

/home/cephadm/.bashrc:
  file.managed:
    - source: salt://bashrc
    - user: cephadm
    - group: users
    - mode: 644
    - template: jinja

/home/ec2-user/.bashrc:
  file.managed:
    - source: salt://bashrc
    - user: ec2-user
    - group: users
    - mode: 644
    - template: jinja

/root/resiliency-data.sh:
  file.managed:
    - source: salt://resiliency-data.sh
    - user: root
    - group: root
    - mode: 755

/root/.bashrc:
  file.managed:
    - source: salt://bashrc
    - user: root
    - group: root
    - mode: 644
    - template: jinja

/etc/sudoers:
  file.managed:
    - source: salt://sudoers
    - user: root
    - group: root
    - mode: 440

/etc/motd:
  file.managed:
    - source: salt://etc-motd
    - user: root
    - group: root
    - mode: 644
    - template: jinja

/home/cephadm/.ssh:
  file.directory:
    - user: cephadm
    - group: users
    - dir_mode: 700

/home/cephadm/.ssh/authorized_keys:
  file.managed:
    - source: salt://id_rsa.pub
    - user: cephadm
    - group: users
    - mode: 600

/home/ec2-user/.ssh/authorized_keys:
  file.append:
    - source: salt://id_rsa.pub

/home/cephadm/.ssh/known_hosts:
  file.managed:
    - user: cephadm
    - group: users
    - mode: 600

/home/ec2-user/.ssh/known_hosts:
  file.managed:
    - user: ec2-user
    - group: users
    - mode: 600

/home/cephadm/.ssh/id_rsa:
  file.managed:
    - source: salt://id_rsa
    - user: cephadm
    - group: users
    - mode: 600

/home/ec2-user/.ssh/id_rsa:
  file.managed:
    - source: salt://id_rsa
    - user: ec2-user
    - group: users
    - mode: 600

/home/cephadm/.ssh/id_rsa.pub:
  file.managed:
    - source: salt://id_rsa.pub
    - user: cephadm
    - group: users
    - mode: 644

/home/ec2-user/.ssh/id_rsa.pub:
  file.managed:
    - source: salt://id_rsa.pub
    - user: ec2-user
    - group: users
    - mode: 644

/etc/sysctl.conf:
  file.managed:
    - source: salt://sysctl.conf
    - user: root
    - group: root
    - mode: 644

/etc/ntp.conf:
  file.managed:
    - source: salt://ntp.conf
    - user: root
    - group: root
    - mode: 644

ntpd:
  service.running:
    - enable: True

ssh-no-interactive.sh-cephadm:
  cmd.script:
    - source: salt://ssh-no-interactive.sh
    - cwd: /home/cephadm
    - user: cephadm
    - template: jinja

ssh-no-interactive.sh-ec2-user:
  cmd.script:
    - source: salt://ssh-no-interactive.sh
    - cwd: /home/ec2-user
    - user: ec2-user
    - template: jinja

