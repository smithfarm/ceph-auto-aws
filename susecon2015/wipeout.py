#!/usr/bin/python
#
# wipeout.py
#
# Wipe out Ceph cluster in AWS.
#
# Generate documentation from #PC comments:
#   $ grep -E '^ *#PC' wipeout.py | sed -e 's/#PC //'g   
#

import argparse
from aws_lib import SpinupError
import init_lib
from os.path import expanduser
from runner_lib import runcommand
import sys
import yaml_lib

#PC * This script (wipeout.py) makes the following assumptions:
#PC     * delegate number provided in argument is really the one you want to
#PC       wipe out
#PC     * each delegate is segregated into his or her own subnet in the YAML
#PC     * these delegate subnets defined in the YAML take the form
#PC       10.0.[d].0/24, where [d] is the delegate number, and these subnets
#PC       really exist
#PC     * "wipe out" operation involves deleting volumes and terminating
#PC       instances (nothing else)
#PC     * in other words, the instances are assumed to use the default security
#PC       group, etc.
#PC     * root volumes are assumed to have the DeleteOnTermination flag set -
#PC       they are not deleted explicitly
#PC     * OSD volumes are assumed to be known to AWS as '/dev/sdb' (regardless
#PC       of how Linux kernel sees them)
#PC     * aws.yaml present in current directory or --yaml option provided;
#PC     * Salt Master exists and is alone in subnet 10.0.0.0/24
#PC     * SSH private key enabling SSH to Salt Master as user ec2-user is
#PC       present in $HOME/.ssh/ec2
#PC     * ec2-user can execute commands as root via sudo without being asked
#PC       for root password
#PC * If the above assumptions are fulfilled, the script should work.
#PC * The following is a high-level description of what the script does.
#PC * Parse command-line arguments.
parser = argparse.ArgumentParser( description='Wipe out a Ceph cluster in AWS.' )
parser.add_argument( 
    '--yaml', 
    default='./aws.yaml', 
    help="yaml file to read (defaults to ./aws.yaml)" 
)
parser.add_argument( 
    'delegate', 
    help="Delegate number to wipe out",
    nargs='?' 
)
args = parser.parse_args()

# Verify that delegate number was given on command line and that it is an integer.
if args.delegate is None:
    raise SpinupError( "Must provide delegate number to wipe out" )
delegate = int(args.delegate)

# Initialize dictionary for storage of globals (values that do not change,
# but are discarded when the script exits).
g = {}

#PC * Parse YAML file.
y = yaml_lib.parse_yaml( args.yaml )

#PC * Connect to region specified in YAML ("region").
# (i.e., get VPCConnection and EC2Connection objects).
# FIXME: validate that the region exists
y['region'] = yaml_lib.yaml_attr( y, 'region', 'eu-west-1' )
( g['vpc_conn'], g['ec2_conn'] ) = init_lib.init_region( y['region'] )
print "Connected to region {}".format( y['region'] )

#PC * Connect to VPC specified in YAML ("vpc" -> "cidr-block").
n = yaml_lib.yaml_attr( y, 'vpc', None )
n['cidr-block'] = yaml_lib.yaml_attr( n, 'cidr-block', None )
n['name'] = yaml_lib.yaml_attr( n, 'name', 'susecon' )
print "Looking for VPC {}".format(n['cidr-block'])
g['vpc_obj'] = init_lib.init_vpc( g['vpc_conn'], n['cidr-block'] )

#PC * Get Salt Master subnet (first one in "subnets" list).
g['master_subnet'] = init_lib.init_subnet( 
    g['vpc_conn'],
    g['vpc_obj'].id,
    y['subnets'][0]['cidr-block']
)

#PC * Get Salt Master instance (i.e., the sole instance in the Salt Master subnet).
g['master_instance'] = init_lib.get_master_instance( 
    g['ec2_conn'], 
    g['master_subnet'].id 
)
print "Salt Master is {}".format( g['master_instance'].ip_address )

#PC * Determine subnet to wipe out.
cidr_block = '10.0.{}.0/24'.format(delegate)

#PC * Get subnet object (raise exception if it doesn't exist).
g['subnet_obj'] = init_lib.init_subnet( g['vpc_conn'], g['vpc_obj'].id, cidr_block )
print "Wiping out all instances in {} (and attached volumes)".format(cidr_block)

#PC * Get all instances in the subnet.
g['instances'] = g['ec2_conn'].get_only_instances( 
    filters={ "subnet-id": g['subnet_obj'].id } 
)

#PC * Loop over the instances, stopping them and detaching their OSD volumes.
g['volumes'] = []
for i in g['instances']:
    vols = g['ec2_conn'].get_all_volumes(
        filters={ "attachment.instance-id": i.id, "attachment.device": "/dev/sdb" }
    )
    g['ec2_conn'].stop_instances( instance_ids=[ i.id ] )
    for v in vols:
        g['volumes'].append((v, i))
        g['ec2_conn'].detach_volume( v.id, instance_id=i.id )

print "Wiping out {} instances and {} attached OSD volumes".format(
    len(g['instances']),
    len(g['volumes'])
)

#PC * Delete the OSD volumes, after waiting for them to really detach.
for mapping in g['volumes']:
    v = mapping[0]
    i = mapping[1]
    init_lib.wait_for_detachment( g['ec2_conn'], v.id, i.id )            
    g['ec2_conn'].delete_volume( v.id )

#PC * Assemble a list of instance IDs to terminate.
id_list = []
for i in g['instances']:
    id_list.append( i.id )

#PC * If there are any instance IDs in that list, terminate them.
if id_list:
    g['ec2_conn'].terminate_instances( instance_ids=id_list )

#PC * Get home directory and construct "$HOME/.ssh/ec2" path to SSH private key
ssh_key_path="{}/.ssh/ec2".format( expanduser("~") )

#PC * Tell the Salt Master to delete any keys associated with this Delegate.
args = [
    "-o",
    "UserKnownHostsFile=/dev/null",
    "-o",
    "StrictHostKeyChecking=no",
    "-i",
    ssh_key_path,
    "-l", 
    "ec2-user",
    g['master_instance'].ip_address.encode("ascii"),
    "sudo salt-key -d 'ip-10-0-{}-*' -y".format(delegate),
]
print "Attempting to run 'salt-key -d' on Salt Master"
( rc, output, err ) = runcommand(
    cmd = 'ssh',
    arguments = args,
    shell = False,
    timeout = 10
)
print output
if rc != 0:
    raise SpinupError( "Error deleting keys on Salt Master: {}".format(err) )

print "Done."
