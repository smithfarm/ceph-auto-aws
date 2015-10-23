# ceph-auto-aws
Automate deployment of Ceph clusters on SLES12 in AWS

## Getting started

First, install the `python-boto` package from the `devel:languages:python` repo. The easiest way to do this may be to visit the page https://build.opensuse.org/package/show/devel:languages:python/python-boto and click on the "Download package" link in the upper right.

Second, clone this git repo to your local machine

Third, put your AWS credentials in `~/.boto` or `~/.aws/credentials` as described [here](http://boto.readthedocs.org/en/latest/getting_started.html#configuring-boto-credentials).

All of the following instructions assume you are *in* the directory containing the local clone.


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
