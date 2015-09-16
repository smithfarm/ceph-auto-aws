#!/usr/bin/python
#
# wipeout.py
#
# Wipe out Ceph cluster in AWS.
#
# Generate pseudo-code from #PC comments:
#   $ grep -E '^ *#PC' aws.py | sed -e 's/#PC //'g   
#

import argparse
from aws_lib import SpinupError
import init_lib
from os.path import expanduser
from runner_lib import runcommand
import sys
import yaml_lib

#PC * Parse arguments.
parser = argparse.ArgumentParser( description='Wipe out a Ceph cluster in AWS.' )
parser.add_argument( 
    '--yaml', 
    default='./aws.yaml', 
    help="yaml file to read (defaults to ./aws.yaml)" 
)
parser.add_argument( 
    'delegate', 
    default='1', 
    help="Delegate number to wipe out",
    nargs='?' 
)
args = parser.parse_args()

# Initialize dictionary for storage of globals (values that do not change,
# but are discarded when the script exits).
g = {}

#PC * Parse YAML.
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

#PC * Get Salt Master subnet.
g['master_subnet'] = init_lib.init_subnet( 
    g['vpc_conn'],
    y['subnets'][0]['cidr-block']
)

#PC * Get Salt Master instance.
g['master_instance'] = init_lib.get_master_instance( 
    g['ec2_conn'], 
    g['master_subnet'].id 
)
print "Salt Master is {}".format( g['master_instance'].ip_address )

#PC * Determine subnet to wipe out.
delegate = int(args.delegate)
cidr_block = '10.0.{}.0/24'.format(delegate)

#PC * Get subnet object (raise exception if it doesn't exist).
g['subnet_obj'] = init_lib.init_subnet( g['vpc_conn'], cidr_block )
print "Wiping out all instances in {} (and attached volumes)".format(cidr_block)

#PC * Get all instances in the subnet.
g['instances'] = g['ec2_conn'].get_only_instances( 
    filters={ "subnet-id": g['subnet_obj'].id } 
)

#PC * Loop over the instances, getting and detaching their OSD volumes ('/dev/sdb').
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
