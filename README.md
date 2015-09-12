# ceph-auto-aws
Automate deployment of Ceph clusters on SLES12 in AWS

Instructions:

1. Put your AWS credentials in `~/.boto` or `~/.aws/credentials` as described [here](http://boto.readthedocs.org/en/latest/getting_started.html#configuring-boto-credentials)
1. Edit the `aws.yaml` file
1. Edit the `user-data-master` script
1. Edit the `user-data-minions` script
1. Run the script `aws.py`.
