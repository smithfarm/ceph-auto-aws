# ceph-auto-aws
Automate deployment of Ceph clusters on SLES12 in AWS

## Getting started

First, install the `python-boto` package from the `devel:languages:python` repo. The easiest way to do this may be to visit the page https://build.opensuse.org/package/show/devel:languages:python/python-boto and click on the "Download package" link in the upper right.

Second, clone this git repo to your local machine

Third, put your AWS credentials in `~/.boto` or `~/.aws/credentials` as described [here](http://boto.readthedocs.org/en/latest/getting_started.html#configuring-boto-credentials)

All of the following instructions assume you are *in* the directory containing the local clone.


## What you can do with this

1. Get list of each delegate's public IP addresses
1. Spin up delegate VMs
1. Deploy Ceph cluster on delegate VMs
1. Wipe out delegates


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

WIP


## How to wipe out delegates

First, make sure you know the delegate number you wish to wipe out and that you really, really want to wipe it out

Second, run the wipeout script, providing the delegate number as the sole argument. For example, the following command wipes out all instances and volumes associated with Delegate No. 3:
```
python wipeout.py 3
```

