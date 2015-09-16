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

#PC * Determine subnet to wipe out.
delegate = int(args.delegate)
cidr_block = '10.0.{}.0/24'.format(delegate)

#PC * Does that subnet even exist?
g['subnet_obj'] = init_lib.init_subnet( g['vpc_conn'], cidr_block )
print g['subnet_obj']

print "Wiping out all instances in {} (and attached volumes)".format(cidr_block)
