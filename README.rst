===========================================
Automate deployment of Ceph clusters in AWS
===========================================

:Author: Nathan Cutler
:License: Creative Commons Attribution-ShareAlike (CC BY-SA)

.. contents::
   :depth: 3

Introduction
============

This document describes how its authors automated deployment of Ceph
clusters in virtual machines on virtual machines provisioned in Amazon Web
Services (AWS) Elastic Computing Cloud (EC2). 

The clusters are intended for use in "hands-on" demonstrations. Attendees
of the hands-on session are referred to herein as "delegates".  Each
delegate gets their own Ceph cluster.

Scripting is provided for automating common tasks such as creating and
wiping out a cluster.

Prerequisites and assumptions
=============================

We assume that you have access to Amazon Web Services (AWS) Elastic
Computing Cloud (EC2) and Virtual Private Cloud (VPC). That means you can login
via a web browser and access the EC2 and VPC dashboards.

This document further assumes you are running a recent (as of March 2016)
openSUSE or SUSE Linux Enterprise platform.

Nothing in this document is guaranteed to work (see License, above).

Early steps
===========

Make an AWS user
----------------

If you are already logged in as an AWS IAM user, you can skip this section.

Set up an IAM user using the `Creating an IAM User in Your AWS Account`_
section of the AWS documentation.

We placed our user in the "ec2_full_access" group.

.. _`Creating an IAM User in Your AWS Account`: http://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html`

Install boto
------------

The scripts use `boto`_, "An integrated interface to current and future
infrastructural services offered by Amazon Web Services."

Fortunately, `boto`_ is packaged for openSUSE. Install the ``python-boto``
package::

    zypper install python-boto

We are using version 2.34.

.. _`boto`: http://boto.cloudhackers.com/en/latest/index.html

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

Test AWS connectivity
---------------------

If you want to test if your credentials are OK, try this::

    $ python
    Python 2.7.8 (default, Sep 30 2014, 15:34:38) [GCC] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import boto
    >>> boto.set_stream_logger('boto')
    >>> ec2 = boto.connect_ec2()
    2016-03-25 21:50:58,859 boto [DEBUG]:Using access key found in config file.
    2016-03-25 21:50:58,860 boto [DEBUG]:Using secret key found in config file.

If your credentials are wrong, the response will be different::

    >>> ec2 = boto.connect_ec2()
    2016-03-25 21:54:46,894 boto [DEBUG]:Retrieving credentials from metadata server.
    2016-03-25 21:54:47,895 boto [ERROR]:Caught exception reading instance data
    ... traceback ...
    2016-03-25 21:54:47,901 boto [ERROR]:Unable to read instance data, giving up
    ... traceback ...
    boto.exception.NoAuthHandlerFound: No handler was ready to
    authenticate. 1 handlers were checked. ['QuerySignatureV2AuthHandler']
    Check your credentials

Clone repo
----------

Clone this repo to your local machine::

    git clone https://github.com/smithfarm/ceph-auto-aws

All of the following instructions assume you are *in* the directory
containing the local clone.

Virtual Private Cloud
=====================

Introduction
------------

To ensure that our demo clusters do not interfere with other AWS projects,
we use a Virtual Private Cloud (VPC).

All the delegates will share a single VPC 10.0.0.0/16. Within that VPC there
will be a ``/24`` subnet for each delegate, plus one for the Salt Master.

The Salt Master resides in its own subnet: 10.0.0.0/24.

Each delegate will be assigned a number, e.g. 12. The subnet of delegate 12
will be 10.0.12.0/24.

Create a VPC
------------

In the VPC dashboard, click on ``Your VPCs`` and then ``Create VPC``.

In the form dialog that appears, enter values::

    Name tag:   handson
    CIDR block: 10.0.0.0/16
    Tenancy:    Default

Click ``Yes, Create``.

Check YAML
----------

All configuration/setup information is placed in the file ``aws.yaml``
which you are expected to edit to suit your needs.

Check and make sure the ``vpc`` stanza (inside the ``aws.yaml`` file in the
current working directory) looks like this::

    vpc:
      cidr-block: 10.0.0.0/16
      name: handson

Validate VPC setup
------------------

Now validate that your VPC is set up properly::

    $ ./list-public-ips.py
    Connected to region eu-west-1
    Looking for VPC 10.0.0.0/16
    There are no instances in the master subnet

Any other output (and especially any traceback) probably means your VPC is
not set up properly.

Subnet caveat
-------------

AWS reserves both the first four IP addresses and the last IP address in
each subnet's CIDR block. For example, in the ``10.0.0.0/24`` subnet, these IP
addresses are not available for use::

* 10.0.0.0: Network address.
* 10.0.0.1: Reserved by AWS for the VPC router.
* 10.0.0.2: Reserved by AWS for mapping to the Amazon-provided DNS.
* 10.0.0.3: Reserved by AWS for future use.
* 10.0.0.255: Network broadcast address. We do not support broadcast in a VPC, therefore we reserve this address. 


## What you can do with this

1. Get list of each delegate's public IP addresses
1. Spin up delegate VMs
1. Deploy Ceph cluster on delegate VMs
1. Wipe out delegate VMs


## How to get list of delegate public IP addresses

This script is also a nice, non-destructive way to check if you have your environment set up correctly.

To run the script, do:
```
./list-public-ips.py
```

Note that the output of this script also includes the public IP address of the Salt Master.


## How to spin up delegate VMs

First, make sure the delegates do not already exist. This can be done either via the Amazon EC2 Web Console or by running the `list-public-ips.py` script.

Second, edit the `aws.yaml` file. Modify the `install_subnets` section so it matches the list of delegates you wish to spin up. For example, the following snippet shows the syntax for installing delegates 1-3:
<pre>
install_subnets:
- 1
- 2
- 3
</pre>

Third, run the spinup script: 
```
python aws.py
```

Note that this step only creates the VMs. To get a running cluster, see the next section.


## How to deploy Ceph cluster on delegate VMs

After the VMs come up, the `salt-minion.service` will be started on each of
them and it will connect to the Salt Master and ask for its key to be accepted.
This can be seen using the following procedure

1. ssh to the Salt Master (IP address can be determined from `list-public-ips.py` output)
1. `sudo -s` to become root
1. `salt-key -L`

In the output of step 3, you should see five unaccepted keys for each delegate you
are spinning up, e.g. after spinning up Delegate 4 I see:
<pre>
Unaccepted Keys:
ip-10-0-4-10.eu-west-1.compute.internal
ip-10-0-4-11.eu-west-1.compute.internal
ip-10-0-4-12.eu-west-1.compute.internal
ip-10-0-4-13.eu-west-1.compute.internal
ip-10-0-4-14.eu-west-1.compute.internal
</pre>

Note the '4' in the hostname indicates Delegate 4.

Next, accept the keys: `salt-key -Ay`

Now that the keys are accepted, you can run the Salt State. Before you do that, 
just a quick check to make sure all the minions are reachable:
<pre>
ip-10-0-0-64:/srv/salt # salt -G 'delegate:4' test.ping
ip-10-0-4-12.eu-west-1.compute.internal:
True
ip-10-0-4-11.eu-west-1.compute.internal:
True
ip-10-0-4-14.eu-west-1.compute.internal:
True
ip-10-0-4-10.eu-west-1.compute.internal:
True
ip-10-0-4-13.eu-west-1.compute.internal:
True
</pre>

If any are not reachable, hold off until they become reachable.

Run the Salt State to prepare all the nodes:

1. `cd /srv/salt` (may not be strictly necessary)
1. `salt -G 'delegate:4' state.sls ceph-admin` (replace '4' with your target delegate number)

This may take some seconds to complete - be patient.

At this point, the nodes are ready to run `ceph-deploy`, which will actually deploy the cluster.
I have written a script to facilitate this.

1. ssh to a delegate's admin node
2. `sudo su - ceph`
3. `./ceph-deploy.sh`
4. `ceph health`

The output from the last command should be `HEALTH_OK`


## How to wipe out delegate VMs

First, make sure you know the delegate number you wish to wipe out and that you really, really want to wipe it out

Second, run the wipeout script, providing the delegate number as the sole argument. For example, the following command wipes out all instances and volumes associated with Delegate No. 3:
```
python wipeout.py 3
```

Note that it does take time for terminated VMs in AWS to actually go away. If
you wipe out a delegate, the VMs will still be present (if terminated) for some
time and that may cause an issue if you try to re-deploy that same delegate.
This needs more testing.
