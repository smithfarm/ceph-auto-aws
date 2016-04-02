#
# dochazka-rest Dockerized testing environment
#
FROM opensuse:42.1
MAINTAINER Nathan Cutler <ncutler@suse.com>

# install "general utility" packages 
RUN zypper --no-gpg-checks --non-interactive install \
    aaa_base \
    aaa_base-extras \
    git \
    glibc-locale \
    python \
    python3 \
    python-virtualenv \
    vim \
    which

# add smithfarm user
RUN useradd -d /home/smithfarm -m -s /bin/bash smithfarm

