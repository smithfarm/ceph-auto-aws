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
addresses are not available for use:

* 10.0.0.0: Network address.
* 10.0.0.1: Reserved by AWS for the VPC router.
* 10.0.0.2: Reserved by AWS for mapping to the Amazon-provided DNS.
* 10.0.0.3: Reserved by AWS for future use.
* 10.0.0.255: Network broadcast address. We do not support broadcast in a VPC, therefore we reserve this address. 


