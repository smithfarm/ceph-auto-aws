===========================================
Automate deployment of Ceph clusters in AWS
===========================================

:Author: Nathan Cutler
:Code license: BSD 3 Clause
:Documentation license: Creative Commons Attribution-ShareAlike (CC BY-SA)

.. contents::
   :depth: 3

Acknowledgements
================

Several parts of this application - especially the command-line interface
design and code - are derived from Loic Dachary's work in `ceph-workbench`_.

.. _`ceph-workbench`: http://ceph-workbench.readthedocs.org/en/latest/

Introduction
============

This document describes the `ceph-auto-aws`_ software for automating deployment
of Ceph clusters in Amazon Web Services (AWS) - specifically the Elastic
Computing Cloud (EC2) and Virtual Private Cloud (VPC) services. 

.. _`ceph-auto-aws`: https://github.com/smithfarm/ceph-auto-aws

The software enables an arbitrary number of identical clusters from 1 to 251 to
be so deployed.

So far, the software has been used in "hands-on" sessions, to provide each attendee
with their own cluster to play with. It could also facilitate deployment of one-off
clusters to test various Ceph configurations.

Scripting is provided for automating the provisioning of:

* a VPC instance
* subnets within the VPC
* cluster instances (nodes) within each subnet
* Salt Master instance (used to control the cluster instances)

The scripting is written in Python and relies on `boto`_ ("An integrated
interface to current and future infrastructural services offered by Amazon Web
Services") and `SaltStack`_ (a configuration management and distributed remote
execution system).

Configuration and state are stored in `YAML`_ file. `YAML`_ is a human friendly
data serialization standard for all programming languages.

.. _`boto`: http://boto.cloudhackers.com/en/latest/index.html
.. _`SaltStack`: https://docs.saltstack.com/en/latest/topics/
.. _`YAML`: http://yaml.org/


Prerequisites and assumptions
=============================

We assume that you have access to Amazon Web Services (AWS) Elastic
Computing Cloud (EC2) and Virtual Private Cloud (VPC). That means you can login
via a web browser and access the EC2 and VPC dashboards.

We further assume that you have a relatively recent version of Python and
`virtualenv`_ installed on your system. On openSUSE, Python should already be
installed and installing `virtualenv`_ should be as simple as running the
following command as root::

    # zypper install python-virtualenv

If something in this software (or this document) doesn't work for you, open a
bug report in the `GitHub issue tracker`_:

.. _`GitHub issue tracker`: https://github.com/smithfarm/ceph-auto-aws/issues

Early steps
===========

Make an AWS user
----------------

If you are already logged in as an AWS IAM user, you can skip this section.

Set up an IAM user using the `Creating an IAM User in Your AWS Account`_
section of the AWS documentation.

We placed our user in the "ec2_full_access" group.

.. _`Creating an IAM User in Your AWS Account`: http://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html`

Obtain access key
-----------------

Access to AWS via boto requires an access key (Access Key ID and Secret
Access Key). For detailed instructions, see the `Getting Your Access Key ID
and Secret Access Key`_ section of the AWS documentation.

The access key comes in a file called "credentials.csv". Put this in a safe
place.

Put your AWS credentials in ``~/.boto`` as described in the 
`Configuring boto credentials section of the boto documentation`_.

.. _`Getting Your Access Key ID and Secret Access Key`: http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html
.. _`Configuring boto credentials section of the boto documentation`: http://boto.readthedocs.org/en/latest/getting_started.html#configuring-boto-credentials

Sample ``~/.boto`` file::

    [Credentials]
    aws_access_key_id = [gobbledygook]
    aws_secret_access_key = [even_longer_gobbledygook]

Clone repo
----------

Clone this repo to your local machine::

    $ git clone https://github.com/smithfarm/ceph-auto-aws

All of the following instructions assume you are *in* the directory
containing the local clone.

Installation
------------

This software is designed to be installed in the standalone virtual Python
environment, implemented with `virtualenv`_.

Installation is a two-step process. First, run the ``bootstrap`` script::

    $ ./bootstrap

This installs the virtual environment in the ``virtualenv/`` directory. The
second step is to activate the `virtualenv`_. The shell prompt changes to
indicate that the virtual environment is active::

    $ source virtualenv/bin/activate
    (virtualenv)$

Use the ``deactivate`` command to leave::

    (virtualenv)$ deactivate
    $

.. _`virtualenv`: https://virtualenv.pypa.io/en/latest/


Get familiar with ho
--------------------

All scripting features are implemented as subcommands of a single script:
``ho`` (an abbreviation of "hands-on")::

    (virtualenv)$ ho --help

Test AWS connectivity
---------------------

Run the following command to test whether you have your AWS
credentials in order::

    (virtualenv)$ ho probe aws
    2016-03-27 20:30:16,554 INFO Connected to AWS EC2

Configuration
=============

YAML file
---------

Interaction with AWS is controlled by a configuration file called ``aws.yaml``.
By default, this file is searched for in the current directory. If it is not
found, a new one will be created.

We assume that you are starting from scratch. To get started, run the following
command::

    (virtualenv)$ ho probe yaml
    2016-03-30 21:35:12,105 INFO Probing 'subnets' stanza
    2016-03-30 21:35:12,105 INFO Loaded yaml tree from './aws.yaml'
    2016-03-30 21:35:12,106 INFO Probing 'keyname' stanza
    2016-03-30 21:35:12,106 INFO Probing 'vpc' stanza
    2016-03-30 21:35:12,108 INFO Probing 'role-definitions' stanza
    2016-03-30 21:35:12,111 INFO Detected roles ['admin', 'windows', 'master', 'mon', 'defaults', 'osd']
    2016-03-30 21:35:12,111 INFO Probing 'region' stanza
    2016-03-30 21:35:12,113 INFO Probing 'cluster-definition' stanza
    2016-03-30 21:35:12,115 INFO Detected cluster-definition stanza
    2016-03-30 21:35:12,115 INFO Detected role 'admin' in cluster definition
    2016-03-30 21:35:12,115 INFO Probing 'delegates' stanza
    2016-03-30 21:35:12,117 INFO Probing 'types' stanza
    2016-03-30 21:35:12,117 INFO YAML tree is sane

You can see that the YAML file has been created::

    (virtualenv)$ file aws.yaml
    aws.yaml: ASCII text

You can run ``ho probe yaml`` anytime to check your configuration file, and
especially after any manual modifications.

Region
------

The next step is to configure the AWS Region. The default is ``eu-west-1``,
i.e. "EU (Ireland)". If you want to use a different region, edit the YAML file
(``aws.yaml`` in current directory) and edit the following line::

    region: eu-west-1

Next, verify that you can connect to that region by running the command::

    (virtualenv)$ ho probe region
    2016-03-30 21:54:34,545 INFO Loaded yaml tree from './aws.yaml'
    2016-03-30 21:54:34,545 INFO Testing connectivity to AWS Region 'eu-west-1'
    2016-03-30 23:02:52,146 INFO Detected 1 VPCs

Virtual Private Cloud
=====================

To ensure that our demo clusters do not interfere with other AWS projects,
we use a Virtual Private Cloud (VPC) containing a number of subnets.

All the delegates will share a single VPC 10.0.0.0/16. Within that VPC there
will be a ``/24`` subnet for each delegate, plus one for the Salt Master.

The Salt Master resides in its own subnet: 10.0.0.0/24.

Each delegate will be assigned a number, e.g. 12. The subnet of delegate 12
will be 10.0.12.0/24.

VPC configuration
-----------------

If you are setting up a VPC for the first time, run the following command to
create one::

    (virtualenv)$ ho install vpc
    2016-03-30 23:20:34,407 INFO Loaded yaml tree from './aws.yaml'
    2016-03-30 23:20:34,686 INFO New VPC ID vpc-cfd7c9aa created with CIDR block 10.0.0.0/16
    2016-03-30 23:20:34,816 INFO Object VPC:vpc-cfd7c9aa tagged with Name=handson

Once the VPC has been created, the ``vpc`` stanza will look like this::

    vpc:
      cidr_block: 10.0.0.0/16
      id: cfd7c9aa

Note that ``ho install vpc`` is idempotent: you can run it as many times as you
want. Try running it a second time::

    (virtualenv)$ ho install vpc
    2016-03-30 23:22:00,612 INFO Loaded yaml tree from './aws.yaml'
    2016-03-30 23:22:00,613 INFO VPC ID according to yaml is vpc-cfd7c9aa
    2016-03-30 23:22:00,907 INFO VPC ID is vpc-cfd7c9aa, CIDR block is 10.0.0.0/16

Any other output (and especially any traceback) probably means your VPC is
not set up properly.

Internet Gateway
----------------

Initially, the VPC will not have an Internet Gateway, and so it will not 
be able to communicate with the outside world in any way (regardless of 
Security Group settings in any instances running inside the VPC). This includes
SSH access into the VPC from outside.

The fact that VPCs are by default completely isolated from the outside world is
by design, but it is not appropriate for a hands-on demonstration.

To remedy this, first create an Internet Gateway and attach it to the VPC. 

**WARNING:** The scripting does not do this step for you!

Route Table
-----------

Even with the Internet Gateway in place, no packets originating from the VPC
will be routed to the outside until a default route is added. This is because
the default Route Table looks like this:

=========== ======= ======= ===========
Destination Target  Status  Propagated
=========== ======= ======= ===========
10.0.0.0/16 local   Active  No
=========== ======= ======= ===========

Add a "default route" line to this table, so it looks like this:

=========== ======= ======= ===========
Destination Target  Status  Propagated
=========== ======= ======= ===========
10.0.0.0/16 local   Active  No
0.0.0.0/0   igw-... Active  No
=========== ======= ======= ===========

**WARNING:** The scripting does not do this step for you!

Network ACL
-----------

Network ACLs are like firewalls at the subnet level. For more information, see
the `Network ACLs chapter of the AWS documentation`_.

.. _`Network ACLs chapter of the AWS documentation`: http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_ACLs.html

Even with the Internet Gateway and the Route Table set up, networking may
still not work as expected inside the VPC. If this is the case, check if
there is a Network ACL associated with your VPC, and check the settings::

    "Security" -> "Network ACLs" in VPC Dashboard

**WARNING:** The scripting does not do this step for you!

Security Groups
---------------

Security Groups are like firewalls at the instance (individual VM) level. For
more information, see the `Security Groups for Your VPC` chapter of the AWS
documentation.

.. _`Security Groups for Your VPC`: http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_SecurityGroups.html

Even with the Internet Gateway and the Route Table set up, and Network ACL wide
open (or disabled), you will still not be able to ping your AWS nodes unless
you edit the Inbound Rules table of your VPC's default Security Group.

You will find it under::

    "Security" -> "Security Groups" in VPC Dashboard

By default, the Inbound Rules table will look like this:

=========== ======== ========== ======
Type        Protocol Port Range Source 
=========== ======== ========== ======
ALL Traffic ALL      ALL        sg-...
=========== ======== ========== ======

Note that only packets originating from within the same Security Group are
accepted. All others are dropped.

Edit the line so Source is set to ``0.0.0.0/0``:

=========== ======== ========== ===========
Type        Protocol Port Range Source
=========== ======== ========== ===========
ALL Traffic ALL      ALL        0.0.0.0/0
=========== ======== ========== ===========

Such a setup means the machines in your VPC will be exposed to scanning, and if
they have any unpatched vulnerabilities evil people might take control of them.

To address this, replace the ``0.0.0.0/0`` line in the Inbound Rules table with
lines covering all the public network segments from which people will be
accessing your VPC.

**WARNING:** The scripting does not do this step for you!

Subnets
=======

As explained in the introduction to the `Virtual Private Cloud`_ chapter,
each delegate will have their own "Class C" ``/24`` virtual network, or
"subnet".

Subnet configuration
--------------------

Initially, the ``subnets`` stanza of your ``aws.yaml`` file should be empty::

    subnets: {}

Do not add anything here: the scripting will create subnets automatically based
on the number of delegates given in the ``delegates`` stanza, e.g.::

    delegates: 1

If you want more than one cluster, change the ``delegates`` stanza in the YAML
file now.

Create subnets
--------------

To ensure that the subnets are created for each delegate plus the Salt Master,
you should run::

    (virtualenv)$ ho install subnets --all --master
    2016-04-03 07:59:03,992 INFO Loaded yaml tree from './aws.yaml'
    2016-04-03 07:59:03,992 INFO Delegate list is [0, 1]
    2016-04-03 07:59:03,992 INFO Installing subnet for delegate 0
    ...

This will create a ``10.0.0.0/24`` subnet for the Salt Master and one
additional ``/24`` for each delegate (one in the default case). It will also
add the appropriate tags to the subnet objects.

Like ``ho install vpc``, this command is idempotent.

Subnet caveat
-------------

AWS reserves both the first four IP addresses and the last IP address in
each subnet's CIDR block. For example, in the ``10.0.0.0/24`` subnet, these IP
addresses are not available for use:

* 10.0.0.0: Network address.
* 10.0.0.1: Reserved by AWS for the VPC router.
* 10.0.0.2: Reserved by AWS for mapping to the Amazon-provided DNS.
* 10.0.0.3: Reserved by AWS for future use.
* 10.0.0.255: Network broadcast address. We do not support broadcast in a VPC,
  therefore we reserve this address. 

For this reason, instances must not be assigned ``last_octet`` values 0, 1, 2,
3, or 255.


Role and cluster definition
===========================

Once the subnets are set up, the next step is to define the cluster each
delegate will receive.

This software assumes that each delegate will have one cluster and all the
clusters will be identical.

Each cluster consists of some number of instances, and each instance has a
"role" that it plays in the cluster. 

**NOTE:** As far as this software is concerned, the term "role" is
interchangeable with "node", "instance" or "virtual machine"!

Before you can install a cluster (or twelve!), you must first edit the `cluster
definition`_ and `role definitions`_ in the yaml.

Role definitions
----------------

Roles are defined in the ``role-definitions`` stanza of the YAML. This stanza
is a mapping, the keys of which are the names of the respective roles. 

There are two special roles: ``default`` and ``master``. The former defines
the set of permissible role attributes and their default values. The latter
defines the attributes of the Salt Master node.

Each role definition may contain one or more of the following attributes:

========================= ====================================================
Role definition attribute Description
========================= ====================================================
ami-id                    AMI ID of image from which to create the instance
last-octet                value of last octet of instance IP address (10.0.0.x)
node-no                   arbitrary number that can optionally be associated
                          with a node
replace-from-environment  FIXME
type                      the Instance Type 
user-data                 file containing user-data
volume                    disk volume to be attached to the instance (optional)
========================= ====================================================

If you are setting up a hands-on, now would be a good time to define your
roles. The following sections should help.

ami-id (REQUIRED)
^^^^^^^^^^^^^^^^^

The ``ami-id`` is the ID of the `Amazon Machine Image (AMI)`_ to use when
provisioning the node. Basically, it should be a recent Linux image that you
are capable of installing Ceph on.

.. _`Amazon Machine Image (AMI)`: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html

last-octet (REQUIRED)
^^^^^^^^^^^^^^^^^^^^^

This attribute should be an integer value between 4 and 254 (inclusive) - see
`Subnet caveat`_. Together with the delegate number, it determines the IP
address of the node. For example, if the delegate number is 3 and
``last-octet`` is 8, the IP address will be ``10.0.3.8/24``.

node-no (OPTIONAL)
^^^^^^^^^^^^^^^^^^

This is an entirely optional value that can be associated with a node. This
number determines what ``@@NODE_NO@@`` in the user-data will be replaced with.

replace-from-environment (OPTIONAL)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

FIXME

type (REQUIRED)
^^^^^^^^^^^^^^^ 

This determines the `Instance Type`_ of the node. If all the nodes will have
the same Instance Type, you can just set it once in the ``defaults`` section.
It does not need to be set individually for each role.

.. _`Instance Type`: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html

The instance types are described at https://aws.amazon.com/ec2/instance-types/

I am using t2.small for cluster nodes and t2.micro for the Salt Master. Both
are single CPU, t2.small has 2 GB of memory and t2.micro has 1 GB.

There are two "types" of instance types: "ebs" and "paravirtual". All the
t2.xxx types are EBS-only. EBS stands for "Elastic Block Store". This is
important to know if you make a snapshot and want to create an AMI from that
snapshot. (Also, I think any volumes you create must be EBS if you want to use
them with t2.xxx instances.)

user-data (OPTIONAL)
^^^^^^^^^^^^^^^^^^^^

After the image boots for the first time, we need to run a custom setup script.
In Cloud terminology this is known as "user-data". Often the user-data takes
form of "cloud-init" YAML. However, with AWS it can be an ordinary shell
script.

For testing, you can type or cut-and-paste user-data in the web console, into
the box located at the very bottom of the "3. Configure Instance" dialog,
hidden under "Advanced Details".

Once you have developed just the right user-data for your application, put it
in a file, and set the ``user-data`` YAML attribute to the absolute or relative
path to this file. Whatever it is, the ``user-data`` in that file will be run
in the instance when it first launches. See `Running Commands on Your Linux
Instance at Launch`_.

.. _`Running Commands on Your Linux Instance at Launch`: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html

This value is optional in the sense that ``ho`` will instantiate nodes without
it, but you will probably need it if you want to automate the process of
installing and starting the Salt Minion service on the nodes.

volume (OPTIONAL)
^^^^^^^^^^^^^^^^^

Each node has a root volume, the size of which is defined by the Instance Type
(VERIFY). This is sufficient for admin nodes and monitor-only nodes. If you
want to run an OSD on a node, though, a separate volume will be necessary.
Typically this will be an `Amazon Elastic Block Store (EBS)`_ volume.

.. _`Amazon Elastic Block Store (EBS)`: https://aws.amazon.com/ebs/

The ``volume`` attribute takes an integer value which is interpreted as the
volume size in  Gigabytes.

If the attribute is missing, or has no value, or has a zero value, no separate
volume is created.

Cluster definition
------------------

Once you have defined the roles, the next step is to stipulate the set of roles
that will constitute a cluster. Remember, each delegate will get one cluster
(one set of roles).

The cluster is defined in the ``cluster-definition`` stanza of the yaml. This
stanza consists of a "collection" (list, array) of instance definitions. Each
instance definition must contain a ``role`` attribute defining the *instance
role*, which should be a very short string (e.g., "mon1") describing the role
this instance will play in the cluster. 

The value of each ``role`` attribute must match one of roles defined in the
``role-definitions`` YAML stanza (see `Role definitions`_).

For example, a reasonable demo cluster might consist of three MON/OSD nodes
(roles ``mon1``, ``mon2``, and ``mon3``, respectively) and an "admin node" with
a public IP address::

    cluster-definition:
      - role: admin
      - role: mon1
      - role: mon2
      - role: mon3

Provided the roles are properly defined in the ``role-definitions`` stanza,
this is a legal cluster definition.

Validation of role and cluster definitions
------------------------------------------

Before you actually try to spin up a cluster, it's a good idea to validate your
YAML::

    (virtualenv)$ ho probe yaml

This command loads the YAML file and performs various validations checks,
including basic sanity checks on the ``cluster-definition`` and
``role-definitions`` stanzas.


Keypairs
========

Before you spin up any Delegate Clusters, you will need to generate delegate
(SSH) keypairs and import them to AWS.

Keyname
-------

The ``keyname`` stanza in the YAML file determines how the keypairs will be
named. If you do nothing, it will be set to your username. If your username is
"regnaw", the Salt Master's keypair will be named ``regnaw-d0``, Delegate 1's
keypair will be ``regnaw-d1``, etc.

If you want the keypair names to be based on some other string, just set the
``keyname`` attribute in the YAML file before continuing.

Generate delegate keypairs
--------------------------

Each delegate will have its own keypair. To generate keypairs for all the
delegates, do::

    $ ./generate-keys.sh

Then, to import them into AWS, do::

    $ ho install keypairs --all --master


Delegates
=========

When newly instantiated nodes boot up for the first time, a script called
``user-data`` is run as root. The idea is for this script to bring the nodes
into a "SaltStack-ready" state - i.e. Salt Master service running on the Salt
Master node, Salt Minion services running on the Delegate Cluster nodes, and
minions communicating with, and accepting orders from, the Salt Master. SSH
access should also be possible using the respective delegate keypair.

To get Ceph running on the cluster nodes, additional steps are necessary. These
steps are accomplished by running `SaltStack`_ commands on the Salt Master
node.

At this point, you should have completed the following steps:

1. ``ho probe aws``
2. ``ho probe yaml``
3. ``ho probe region``
4. ``ho install vpc``
5. create Internet Gateway in VPC Console
6. ``ho install subnets --all --master``
7. define roles (by editing the YAML file)
8. define cluster (by editing the YAML file)
9. ``./generate-keys.sh``
10. ``ho install keypairs --all --master``
11. write user-data script for the Salt Master
12. set ``user-data`` attribute of ``master`` role to filename of Salt Master
    user-data script
13. write user-data scripts for all your roles
14. set ``user-data`` attribute of all roles to the appropriate filename

Now you are ready to instantiate nodes. We start with the Salt Master node.

Install Salt Master
-------------------

Delegate 0 is the Salt Master, but we do not write, e.g., ``ho install delegate
0``. Instead, we pass the ``--master`` option like so::

    $ ho install delegate --master

.. Theoretically, it is possible to instantiate the Salt Master node and all
.. the Delegate Cluster nodes at once by doing::
.. 
..     $ ho install delegate --all --master
.. 
.. In practice, this will not work. The nodes will be instantiated and the
.. ``user-data`` scripts will run. However, tis not recommended, however, because it's a good idea to let the Salt
.. Master node "settle" and verify its proper functioning before instantiating any
.. Delegate Cluster nodes, since these nodes will typically have ``user-data``
.. scripts that automate registration of minion keys with the Salt Master.
.. 
It is a good idea to wait until the Salt Master boots up for the first time and
finishes running its user-data script before installing any Delegate Clusters.

.. Once the SSH service is running, you can SSH into the Salt Master. Then you can
.. tail the logs in FIXME like so::
.. 
..     $ FIXME FIXME FIXME TAIL THE USER-DATA LOGS


Install Delegate Clusters
-------------------------

This software is capable of automating the installation of multiple Delegate
Clusters - up to the number set in the ``delegates`` stanza of the YAML file.

If you are just testing the software, it's probably a good idea not to set
``delegates`` too high. You could set a value of 1 to start with::

    cluster-definition:
      - role: admin

    delegates: 1

    ...

The ``delegates`` stanza limits the number of clusters that can be instantiated
at once (or at all). A value of 1 means that the ``ho install delegates``
command will only take an argument of 1. Any other argument will fail. If you
specify ``--all``, it will mean 1.

With the above YAML a single Delegate Cluster will be installed when you run::

    $ ho install delegates 1

The cluster will consist of a single admin node which will be instantiated in
the ``10.0.1.0/24`` subnet.

Instance tagging
----------------

Automatically, each cluster instance will be tagged as follows:

======== ===========================================
Tag      Description
======== ===========================================
Name     the value of the ``nametag`` yaml attribute
Delegate the delegate number
Role     the instance role
======== ===========================================

Stop and start clusters
=======================

You can stop and start clusters using the ``ho stop delegates`` and ``ho start
delegates`` commands, respectively. "Stop" in this context triggers an orderly
shutdown, so it involves a transition to "powered-off" state. "Start", then, is
conceptually similar to powering up.

For example::

    $ ho stop delegates 1
    $ ho stop delegates 1,3,5-7
    $ ho stop delegates --all
    $ ho stop delegates --all --master

    $ ho start delegates 1
    $ ho start delegates 1,3,5-7
    $ ho start delegates --all
    $ ho start delegates --all --master

The ``--master`` option adds delegate 0 (the Salt Master) to the list of
delegates to which the operation (start or stop) is applied.

Wipeout clusters
================

When you are finished with a cluster (or clusters), you can delete it/them
by::

    $ ho wipeout delegates [DELEGATE_LIST]

where ``[DELEGATE_LIST]`` is something like ``1-12`` for Delegate Clusters one
through twelve, ``5`` for Delegate Cluster five, or ``1,3,7-9`` for Delegate
Clusers one, three, seven, eight, and nine.

Sticking to our minimal example from `Install Delegate Clusters`_, we could
wipe out that cluster by::

    $ ho wipeout delegates 1

When you are finished with the Salt Master, you can delete it by adding
the ``--master`` option, e.g.::

    $ ho wipeout delegates --master

You can wipe out all instances, i.e all Delegate Clusters and the Salt
Master, like so::

    $ ho wipeout delegates --all --master

**NOTE:** The wipeout commands discussed in this section remove cluster nodes
and EBS volumes only. They do not have any effect on subnets or the VPC. (If
needed, those must be wiped out separately.)

Spin up a Delegate Cluster
==========================

Take the following example::

    cluster-definition:
      - role: admin
      - role: mon1
      - role: mon2
      - role: mon3
      - role: windows

    ...

    role-definitions:
      admin:
        last-octet: 10
        volume:
      defaults:
        ami-id: ami-ff63dd8c
        last-octet:
        replace-from-environment: []
        type: t2.small
        user-data: data/user-data-nodes
        volume: 20
      master:
        last-octet: 10
        user-data: data/user-data-master
        volume:
      mon1:
        last-octet: 11
        volume: 20
      mon2:
        last-octet: 12
        volume: 20
      mon3:
        last-octet: 13
        volume: 20
      osd:
        last-octet: 14
        volume: 20
      windows:
        ami-id: ami-c6972fb5
        last-octet: 15
        user-data: data/user-data-windows
        volume:

The ``user-data-nodes`` script updates each cluster node and adds the repo
containing the latest versions of the ``ceph`` and ``ceph-deploy`` packages.  
It also configures and enables the ``ntp`` and ``salt-minion`` services.

One can follow progress of the user-data script on a given node by sshing into 
the node and doing::

    (Cluster Node)# tail -n 100 -f /var/log/cloud-init-output.log

Once all the cluster nodes have finished running their user-data scripts, you
can SSH to the Salt Master and list the minion keys::

    (Salt Master)# salt-key -L

This shows the unaccepted keys. Accept them by doing::

    (Salt Master)# salt-key -A -y

If there are stale keys from clusters that have been wiped out, you can just
delete all keys and wait for the live minions to re-connect::

    (Salt Master)# salt-key -A -y

The next step is to run the ``ceph-admin`` Salt State on all the nodes. In this
example we are spinning up a cluster for Delegate 2::

    (Salt Master)# salt -C "G@delegate:2" state.sls ceph-admin

Examine **all** the output. If there are failures, just run the command over
again. Once it is completing without any failures, remotely run the
``ceph-deploy-sh`` Salt State on the admin node to deploy a Ceph cluster::

    (Salt Master)# salt -C "G@delegate:2 and G@role:admin" state.sls ceph-deploy-sh

This will take a minute or two to complete. If all goes well, it will succeed.
If it fails, you have no choice but to wipe out the delegate and start over.

Of course, the gold standard of a well-functioning Ceph cluster is
``HEALTH_OK``. Check the cluster health by running the ``ceph-s`` Salt State::

    (Salt Master)# salt -C "G@delegate:2 and G@role:admin" state.sls ceph-s

If you want to fill the cluster partially up with some data, do::

    (Salt Master)# salt -C "G@delegate:2 and G@role:mon1" state.sls owen-data-sh

At this point, you can SSH into the Delegate 2 admin node and become user "ceph" by doing::

    (Delegate 2 admin node)# su - ceph

Lessons Learned from Snow Unix 2016
===================================

The following lessons were learned:

* double-check instance limit
* practice spinning up the full number of delegates (not just once, but several
  times in a row)
* figure out how best to freeze the state so we no longer run "zypper up",
  exposing ourselves to the risk of a new kernel, etc. coming out

Other miscellaneous notes
=========================

Package Updates
---------------

Once a SLES image boots up, the first thing you need to do is "zypper up".
Once nice feature of AWS is that it has its own internal SMT server. However,
it takes some seconds after boot for the the associated zypper service to
appear. Therefore, we use the following loop in the user-data script:

while sleep 10 ; do
    zypper services | grep 'SMT-http_smt-ec2_susecloud_net'
    if [[ $? = 0 ]] ; then
        break
    fi  
done

After that completes, you can assume that the basic repos are available, so you
can do "zypper up" as follows:

while sleep 5 ; do
    zypper -n update
    if [[ $? = 0 ]] ; then
        break
    fi
done


SUSE Enterprise Storage repos
-----------------------------

Unfortunately, the AWS SMT server only has the basic SLES pool and update
repos. No SUSE Enterprise Storage or any other add-ons for that matter.
So we have to make our own installation sources. The way I ended up doing
that was to loop mount the SES2 GA ISO on the Salt Master and run an apache2
server there to make it available to the delegate instances.

First, append the ISO to /etc/fstab::

    $MEDIA_FULL_PATH /srv/repos/SES2-media1 iso9660 loop 0 0

Second, mount the ISO::

    mount /srv/repos/SES2-media1

Third, set up Apache::

    # zypper in apache2
    # systemctl enable apache2.service
    # echo "I am a puppet" > /srv/repos/puppet.txt
    # vim /etc/apache2/vhosts.d/admin.conf

    <VirtualHost *:80>
        ServerAdmin presnypreklad@gmail.com
        ServerName admin
        DocumentRoot /srv/repos
        HostnameLookups Off
        UseCanonicalName Off
        ServerSignature On
        <Directory /srv/repos>
            Options Indexes FollowSymLinks
            AllowOverride All
            Require all granted
        </Directory>
    </VirtualHost>

    # systemctl restart apache2.service
    # curl http://localhost/puppet.txt
    I am a puppet

Fourth, try the curl command from another machine in the cluster.

Fifth, add the repo on the cluster nodes::

    # zypper ar http://localhost/SES2/ SES2
    Adding repository 'SES2' ......................................................[done]
    Repository 'SES2' successfully added
    Enabled     : Yes                  
    Autorefresh : No                   
    GPG Check   : Yes                  
    URI         : http://localhost/SES2

Sixth, install Ceph packages from the ISO on the cluster nodes
(use SaltStack for this).


Logging user-data script output
===============================

Source: https://alestic.com/2010/12/ec2-user-data-output/

As the user-data script runs, its output is logged to a file called::

    /var/log/cloud-init-output.log


Adding tags to instances after run_instances
--------------------------------------------

http://stackoverflow.com/questions/8070186/boto-ec2-create-an-instance-with-tags


SaltStack notes
===============

Ping all machines belonging to a given delegate:

# salt -G 'delegate:12' test.ping

Get IP addresses of all machines belonging to the delegate:

# salt -G 'delegate:12' network.ip_addrs

Compound match: get IP address of Delegate 12's admin node:

# salt -C 'G@delegate:1 and G@role:admin' network.ip_addrs



Windows change administrator password via user-data script
==========================================================

<script>net user Administrator GieGh7ie</script>

