===========================================
Automate deployment of Ceph clusters in AWS
===========================================

:Author: Nathan Cutler
:Code license: BSD 3 Clause
:Documentation license: Creative Commons Attribution-ShareAlike (CC BY-SA)

.. contents::
   :depth: 3

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

Nothing in this document is guaranteed to work (see the licenses, above).

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

    (virtualenv)$ ho probe vpc
    2016-03-30 23:20:34,407 INFO Loaded yaml tree from './aws.yaml'
    2016-03-30 23:20:34,686 INFO New VPC ID vpc-cfd7c9aa created with CIDR block 10.0.0.0/16
    2016-03-30 23:20:34,816 INFO Object VPC:vpc-cfd7c9aa tagged with Name=handson

Once the VPC has been created, the ``vpc`` stanza will look like this::

    vpc:
      cidr_block: 10.0.0.0/16
      id: cfd7c9aa

Note that ``ho probe vpc`` is idempotent: you can run it as many times as you
want. Try running it a second time::

    (virtualenv)$ ho probe vpc
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
open or disabled, networking may still not work as expected inside the VPC. If
this is the case, check if there are any Security Groups associated with your
VPC::

    "Security" -> "Security Groups" in VPC Dashboard

Initially, you can set the inbound and outbound rules of your VPC's default
Security Group to "wide open" like this:

**Inbound Rules**

=========== ======== ========== ===========
Type        Protocol Port Range Source
=========== ======== ========== ===========
ALL Traffic ALL      ALL        sg-...
=========== ======== ========== ===========

**Outbound Rules**

=========== ======== ========== ===========
Type        Protocol Port Range Destination
=========== ======== ========== ===========
ALL Traffic ALL      ALL        0.0.0.0/0
=========== ======== ========== ===========

However, such a setup means the machines in your VPC will be exposed to
scanning, and if they have any unpatched vulnerabilities evil people might take
control of them.

To address this, remove those lines and add inbound/outbound rules covering all
the public network segments from which people will be accessing your VPC.

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

Validate subnets
----------------

To ensure that the subnets are created for each delegate plus the Salt Master,
you should run::

    (virtualenv)$ ho probe subnets
    2016-03-31 00:02:15,915 INFO Loaded yaml tree from './aws.yaml'
    2016-03-31 00:02:15,916 INFO Probing 1 subnets
    2016-03-31 00:02:15,916 INFO VPC ID according to yaml is vpc-cfd7c9aa
    2016-03-31 00:02:16,175 INFO VPC ID is vpc-cfd7c9aa, CIDR block is 10.0.0.0/16
    2016-03-31 00:02:16,379 INFO Created subnet subnet-6bfb121d (10.0.0.0/24)
    2016-03-31 00:02:16,520 INFO Object Subnet:subnet-6bfb121d tagged with Name=handson
    2016-03-31 00:02:16,643 INFO Object Subnet:subnet-6bfb121d tagged with Delegate=0
    2016-03-31 00:02:16,644 INFO VPC ID according to yaml is vpc-cfd7c9aa
    2016-03-31 00:02:16,912 INFO VPC ID is vpc-cfd7c9aa, CIDR block is 10.0.0.0/16
    2016-03-31 00:02:17,097 INFO Created subnet subnet-68fb121e (10.0.1.0/24)
    2016-03-31 00:02:17,230 INFO Object Subnet:subnet-68fb121e tagged with Name=handson
    2016-03-31 00:02:17,358 INFO Object Subnet:subnet-68fb121e tagged with Delegate=1
    ...

This will create a ``10.0.0.0/24`` subnet for the Salt Master and one
additional ``/24`` for each delegate. It will also add the appropriate tags to
the subnet objects.


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

Instances
=========

Once the subnets are set up, the next step is to install a set of
clusters/delegates.

This software assumes that each delegate will have one cluster and all the
clusters will be identical.

Each cluster consists of some number of instances, and each instance has a role
that it plays in the cluster.

Before you can install a cluster (or twelve!), you must first edit the `cluster
definition`_ and `role definitions`_ in the yaml.

Cluster definition
------------------

The cluster is defined in the ``cluster-definition`` stanza of the yaml. This
stanza consists of an array of instance definitions. Each instance definition
must contain a ``role`` attribute defining the *instance role*, which should be
a very short string (e.g., "mon1") describing the role this instance will play
in the cluster. 

The value of each ``role`` attribute must match one of roles defined in the
``roles`` yaml stanza.

To validate the cluster definition, do::

    (virtualenv)$ ho probe cluster-definition

This command loads the yaml file and performs various checks on the
``cluster-definition`` attribute.

Role definitions
----------------

The roles themselves are defined in the ``roles`` section of the yaml, which
contains a set of name-value pairs. The name is the role name, and the
value is the role definition.

Each role definition may contain one or more of the following attributes:

========================= ====================================================
Role definition attribute Description
========================= ====================================================
ami-id                    the AMI ID of the image from which to create the instance
replace-from-environment  FIXME
type                      the Instance Type 
user-data                 file containing user-data
volume                    disk volume to be attached to the instance (optional)
========================= ====================================================

If an attribute is missing, the default is taken. Defaults are defined in a
special role called ``defaults``.

To validate the role definitions, do::

    (virtualenv)$ ho probe roles

This command loads the yaml file and performs various checks on the
``roles`` attribute.

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

