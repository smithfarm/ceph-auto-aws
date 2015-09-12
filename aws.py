#!/usr/bin/python
#
# aws.py
#
# Spin up Ceph cluster in AWS.
#
# Cluster is defined in the aws.yaml file.
#

import argparse
from aws_lib import SpinupError
import init_lib
from pprint import pprint
import sys
import yaml_lib

# Parse arguments.
parser = argparse.ArgumentParser( description='Spin up a Ceph cluster in AWS.' )
parser.add_argument( 
    '--yaml', 
    default='./aws.yaml', 
    help="yaml file to read (defaults to ./aws.yaml)" 
)
parser.add_argument( 
    'operation', 
    default='create', 
    help="cluster-wide cloud operation ('create', 'terminate', 'pause', "+
         "'resume', 'start', 'stop', 'suspend', 'unpause') to perform",
    nargs='?' 
)
args = parser.parse_args()

# Initialize dictionary for storage of globals, which are temporary
# values which do not change, but are discarded when the script exits
g = {}

# Parse YAML
y = yaml_lib.parse_yaml( args.yaml )

# Connect to our region (i.e., get VPCConnection and EC2Connection objects)
y['region'] = yaml_lib.yaml_attr( y, 'region', 'eu-west-1' )
( g['vpc_conn'], g['ec2_conn'] ) = init_lib.init_region( y['region'] )
print "Connected to region {}".format( y['region'] )

# Get VPC object
n = yaml_lib.yaml_attr( y, 'vpc', None )
n['id'] = yaml_lib.yaml_attr( n, 'id', None )
n['cidr-block'] = yaml_lib.yaml_attr( n, 'cidr-block', None )
print "Looking for VPC {} ({})".format(n['id'], n['cidr-block'])
g['vpc_obj'] = init_lib.init_vpc( g['vpc_conn'], n['id'] )
if n['cidr-block'] == g['vpc_obj'].cidr_block:
    print "Found VPC {} ({})".format(n['id'], n['cidr-block'])
else:
    raise SpinupError( "Found VPC {} but its cidr-block attribute is {} (we were expecting {})".format(
        g['vpc_obj'].id,
        g['vpc_obj'].cidr_block,
        n['cidr-block']
    ) )

# Get subnet objects
n = yaml_lib.yaml_attr( y, 'subnets', None )
print "{} subnets in yaml".format(len(n))
if 1 > len(n):
    raise SpinupError( "No subnets in yaml" )
count = 0
g['subnet_obj'] = []
for s in n:
    print "Looking for subnet {} ({})".format(s['id'], s['cidr-block'])
    g['subnet_obj'].append( init_lib.init_subnet( g['vpc_conn'], s['id'] ) )
    if s['cidr-block'] == g['subnet_obj'][count].cidr_block:
        print "Found subnet {} ({})".format(s['id'], s['cidr-block'])
        if g['subnet_obj'][count].mapPublicIpOnLaunch == 'false':
            init_lib.set_subnet_map_public_ip( g['ec2_conn'], s['id'] )
    else:
        raise SpinupError( "Found VPC {} but its cidr-block attribute is {} (we were expecting {})".format(
            g['subnet_obj'][count].id,
            g['subnet_obj'][count].cidr_block,
            s['cidr-block']
        ) )
    count += 1

# Non-create operations.
operation = args.operation.lower()
if operation != 'create':
    # FIXME: perform the operation
    raise SpinupError( "Operation {} not implemented".format(operation) )

# Create operation.

# Admin node.

# Prepare user-data.
u = init_lib.read_user_data( y['admin']['user-data'] )
u = init_lib.init_sleskey( u )
u = init_lib.init_email( u )
print u
