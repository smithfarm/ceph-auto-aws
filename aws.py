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
    '--master', 
    action='store_const', 
    const=True,
    help="Install the Salt Master in 10.0.0.0/24"
)
parser.add_argument( 
    'operation', 
    default='create', 
    help="cluster-wide cloud operation ('create', 'terminate', 'pause', "+
         "'resume', 'start', 'stop', 'suspend', 'unpause') to perform",
    nargs='?' 
)
args = parser.parse_args()

# Initialize dictionary for storage of globals (values that do not change,
# but are discarded when the script exits).
g = {}

# Parse YAML.
y = yaml_lib.parse_yaml( args.yaml )

# Connect to our region (i.e., get VPCConnection and EC2Connection objects).
y['region'] = yaml_lib.yaml_attr( y, 'region', 'eu-west-1' )
( g['vpc_conn'], g['ec2_conn'] ) = init_lib.init_region( y['region'] )
print "Connected to region {}".format( y['region'] )

# Get VPC object and make sure name is set.
n = yaml_lib.yaml_attr( y, 'vpc', None )
n['cidr-block'] = yaml_lib.yaml_attr( n, 'cidr-block', None )
n['name'] = yaml_lib.yaml_attr( n, 'name', 'susecon' )
print "Looking for VPC {}".format(n['cidr-block'])
g['vpc_obj'] = init_lib.init_vpc( g['vpc_conn'], n['cidr-block'] )
init_lib.update_name( g['vpc_obj'], n['name'] )
print "Found VPC {} (Name: {})".format(n['cidr-block'], n['name'])

# Get subnet objects and make sure names are set.
subnets = yaml_lib.yaml_attr( y, 'subnets', None )
print "{} subnets in yaml".format(len(subnets))
if 1 > len(n):
    raise SpinupError( "No subnets in yaml" )
count = 0
g['subnet_obj'] = []
count = 0
for s in subnets:
    if count == 0:
        # master subnet
        s['name'] = yaml_lib.yaml_attr( s, 'name', 'master' )
        s['cidr-block'] = yaml_lib.yaml_attr( s, 'cidr-block', '10.0.0.0/24' )
        print "Looking for master subnet {} ({})".format(s['cidr-block'], s['name'])
    else:
        # minion subnet
        s['name'] = yaml_lib.yaml_attr( s, 'name', None )
        s['cidr-block'] = yaml_lib.yaml_attr( s, 'cidr-block', '10.0.{}.0/24'.format(count) )
        print "Looking for minion subnet {} ({})".format(s['cidr-block'], s['name'])
    # Get subnet object and append it to globals storage.
    g['subnet_obj'].append( init_lib.init_subnet( g['vpc_conn'], s['cidr-block'] ) )
    # Update subnet name.
    init_lib.update_name( g['subnet_obj'][count], s['name'] )
    # Update subnet "MapPublicIpOnLaunch" attribute.
    if g['subnet_obj'][count].mapPublicIpOnLaunch == 'false':
        init_lib.set_subnet_map_public_ip( g['ec2_conn'], g['subnet_obj'][count].id )
    print "Found subnet {} ({})".format(s['cidr-block'], s['name'])
    count += 1

# Was --master given?
if args.master:
    # FIXME: implement master node provisioning from user-data-master
    raise SpinupError( "You specified --master, but this feature is not ready yet." )
else:
    # Check that master exists and get its public_ipv4
    instances = g['ec2_conn'].get_only_instances( filters={ "subnet-id": g['subnet_obj'][0].id } )
    if 1 > len(instances):
        raise SpinupError( "There are no instances in the master subnet" )
    if 1 < len(instances):
        raise SpinupError( "There are too many instances in the master subnet" )
    g['master_instance'] = instances[0]
    init_lib.update_name( g['master_instance'], 'master' )
    print "Found master instance {}, {}, {}".format( 
        g['master_instance'].id, 
        g['master_instance'].ip_address,
        g['master_instance'].private_ip_address
    )

# Non-create operations.
operation = args.operation.lower()
if operation != 'create':
    # FIXME: perform the operation
    raise SpinupError( "Operation {} not implemented".format(operation) )

# Look at how many subnets we're installing.
y['install_subnets'] = yaml_lib.yaml_attr( y, 'install_subnets', None )
n = len(y['install_subnets'])
print "Installing {} of {} subnet(s)".format(n, len(subnets))

# Sanity checks on subnets.
for n in y['install_subnets']:
    if n < 0:
        raise SpinupError( "No negative subnets, silly" )
    if n == 0:
        raise SpinupError( "Use --master to install the master subnet 10.0.0.0/24" )
    if n > len(subnets):
        raise SpinupError( "Subnet {} is to be installed, but only {} subnets are defined in yaml".format(n, len(subnets)) )

# Create operation on install_subnets specified in yaml.
g['subnets'] = {}
for c in y['install_subnets']:
    subnet_id = g['subnet_obj'][c].id
    subnet_cidr = g['subnet_obj'][c].cidr_block
    print "Installing subnet {} ({})".format( subnet_cidr, subnet_id )
    # Get all existing instances in the subnet.
    existing_instances = g['ec2_conn'].get_all_instances(
        filters={ "subnet-id": subnet_id }
    )
    noofinstances = len(existing_instances)
    if noofinstances > 0:
        print "There are {} existing instances in subnet {}".format(noofinstances, subnet_id)
        for i in existing_instances:
            print i.id
        #sys.exit(1)

    # Admin node.
    print "Create admin node"
    reservation = init_lib.make_reservation( 
        g['ec2_conn'], 
        y['admin']['ami'],
        key_name=y['keyname'],
        instance_type=y['admin']['type'],
        user_data=y['admin']['user-data'],
        subnet_id=subnet_id
    )

