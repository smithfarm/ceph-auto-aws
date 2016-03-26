#!/usr/bin/python
#
# stop.py
#
# Stop a Ceph cluster in AWS.
#
# Generate documentation from #PC comments:
#   $ grep -E '^ *#PC' stop.py | sed -e 's/#PC //'g   
#

import argparse
from aws_lib import SpinupError
import init_lib
from os.path import expanduser
from runner_lib import runcommand
import sys
import yaml_lib

#PC * This script (stop.py) makes the following assumptions:
#PC     * delegate number provided in argument is really the one you want to
#PC       stop
#PC     * each delegate is segregated into his or her own subnet in the YAML
#PC     * these delegate subnets defined in the YAML take the form
#PC       10.0.[d].0/24, where [d] is the delegate number, and these subnets
#PC       really exist
#PC     * "stop" operation involves stopping instances (nothing else)
#PC     * in other words, the instances are assumed to use the default security
#PC       group, etc.
#PC     * aws.yaml present in current directory or --yaml option provided;
#PC     * Salt Master exists and is alone in subnet 10.0.0.0/24
#PC * If the above assumptions are fulfilled, the script should work.
#PC * The following is a high-level description of what the script does.
#PC * Parse command-line arguments.
parser = argparse.ArgumentParser( description='Stop a Ceph cluster in AWS.' )
parser.add_argument( 
    '--yaml', 
    default='./aws.yaml', 
    help="yaml file to read (defaults to ./aws.yaml)" 
)
parser.add_argument( 
    'delegate', 
    help="Delegate number to stop",
    nargs='?' 
)
args = parser.parse_args()

# Verify that delegate number was given on command line and that it is an integer.
if args.delegate is None:
    raise SpinupError( "Must provide delegate number to stop" )
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

#PC * Determine subnet to stop.
cidr_block = '10.0.{}.0/24'.format(delegate)

#PC * Get subnet object (raise exception if it doesn't exist).
g['subnet_obj'] = init_lib.init_subnet( g['vpc_conn'], g['vpc_obj'].id, cidr_block )
print "Stopping all instances in {} (and attached volumes)".format(cidr_block)

#PC * Get all instances in the subnet.
g['instances'] = g['ec2_conn'].get_only_instances( 
    filters={ "subnet-id": g['subnet_obj'].id } 
)

#PC * Loop over the instances, stopping them.
g['volumes'] = []
for i in g['instances']:
    g['ec2_conn'].stop_instances( instance_ids=[ i.id ] )

print "Done."
