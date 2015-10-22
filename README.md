# ceph-auto-aws
Automate deployment of Ceph clusters on SLES12 in AWS

## Getting started

1. Clone the repo to your local machine
1. Put your AWS credentials in `~/.boto` or `~/.aws/credentials` as described [here](http://boto.readthedocs.org/en/latest/getting_started.html#configuring-boto-credentials)

## What you can do with this

1. Spin up delegates
1. Wipe out delegates
1. Get list of each delegate's public IP addresses

## How to spin up delegates

First, make sure the delegates do not already exist

Second, edit the `aws.yaml` file. Modify the `install_subnets` section so it matches the list of delegates you wish to spin up, e.g.:
<pre>
install_subnets:
- 1
- 2
- 3
</pre>

Third, run the spinup script: 
    python aws.py

## How to wipe out delegates

1. Make sure you know the delegate number you wish to wipe out and that you really, really want to wipe it out
1. Run the wipeout script, providing the delegate number as the sole argument, e.g.:

    python wipeout.py 3

## How to get list of delegate public IP addresses

Run the script:
    python list-public-ips.py
