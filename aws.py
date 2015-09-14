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
init_lib.update_tag( g['vpc_obj'], 'Name', n['name'] )
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
    init_lib.update_tag( g['subnet_obj'][count], 'Name', s['name'] )
    # Update subnet "MapPublicIpOnLaunch" attribute.
    if g['subnet_obj'][count].mapPublicIpOnLaunch == 'false':
        init_lib.set_subnet_map_public_ip( g['ec2_conn'], g['subnet_obj'][count].id )
    print "Found subnet {} ({})".format(s['cidr-block'], s['name'])
    count += 1

# Was --master given?
if args.master:
    # One master node.
    print "Create 1 master node"
    u = process_user_data( y['master']['user-data'], y['master']['replace-from-environment'] )
    reservation = init_lib.make_reservation( 
        g['ec2_conn'], 
        y['master']['ami-id'],
        1,
        key_name=y['keyname'],
        instance_type=y['master']['type'],
        user_data=y['master']['user-data'],
        subnet_id=g['subnet_obj'][0].id,
        master=True
    )
    g['master'] = reservation.instances[0]
    init_lib.update_tag( g['master'], 'Name', 'master' )
    print "Master node {} ({}, {}) created.".format(
        g['master_instance'].id, 
        g['master_instance'].ip_address,
        g['master_instance'].private_ip_address
    )
    sys.exit(0)
else:
    # Check that master exists and get its public_ipv4
    instances = g['ec2_conn'].get_only_instances( filters={ "subnet-id": g['subnet_obj'][0].id } )
    if 1 > len(instances):
        raise SpinupError( "There are no instances in the master subnet" )
    if 1 < len(instances):
        raise SpinupError( "There are too many instances in the master subnet" )
    g['master_instance'] = instances[0]
    init_lib.update_tag( g['master_instance'], 'Name', 'master' )
    print "Found master instance {} ({}, {})".format( 
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

# Initialize structures to hold the resource objects we will be creating.
g['admin_node'] = {}
g['mon1_node'] = {}
g['mon2_node'] = {}
g['mon3_node'] = {}
volume_size = yaml_lib.yaml_attr( y['mon'], 'volume', 20 )
for delegate in y['install_subnets']:
    g['admin_node'][delegate] = {}
    g['mon1_node'][delegate] = {}
    g['mon2_node'][delegate] = {}
    g['mon3_node'][delegate] = {}
    
# Create operation on install_subnets specified in yaml.
for delegate in y['install_subnets']:
    subnet_id = g['subnet_obj'][delegate].id
    subnet_cidr = g['subnet_obj'][delegate].cidr_block
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

    # One admin node.
    print "Create 1 admin node"
    u = process_user_data( y['admin']['user-data'], y['admin']['replace-from-environment'] )
    reservation = init_lib.make_reservation( 
        g['ec2_conn'], 
        y['admin']['ami-id'],
        1,
        key_name=y['keyname'],
        instance_type=y['admin']['type'],
        user_data=u,
        subnet_id=subnet_id,
        master=False
        master_ip=g['master_instance'].private_ip_address,
        delegate_no=delegate
    )
    g['admin_node'][delegate]['instance'] = reservation.instances[0]
    init_lib.update_tag( g['admin_node'][delegate]['instance'], 'Name', 'admin' )
    init_lib.update_tag( g['admin_node'][delegate]['instance'], 'Delegate', delegate )

    # Three mon nodes.
    print "Create 3 mon nodes"
    u = process_user_data( y['mon']['user-data'], y['mon']['replace-from-environment'] )
    reservation = init_lib.make_reservation( 
        g['ec2_conn'], 
        y['mon']['ami-id'],
        3,
        key_name=y['keyname'],
        instance_type=y['mon']['type'],
        user_data=u,
        subnet_id=subnet_id,
        master=False,
        master_ip=g['master_instance'].private_ip_address,
        delegate_no=delegate
    )
    for x in range(1, 4):
        mon_node = g['mon{}_node'.format(x)][delegate]
        mon_node['instance'] = reservation.instances[x-1]
        init_lib.update_tag( mon_node['instance'], 'Name', 'mon' )
        init_lib.update_tag( mon_node['instance'], 'Delegate', delegate )
        mon_node['volume'] = g['ec2_conn'].create_volume( volume_size, mon_node['instance'].placement )
    for x in range(1, 4):
        mon_node = g['mon{}_node'.format(x)][delegate]
        instance = mon_node['instance']
        volume = mon_node['volume']
        init_lib.wait_for_running( g['ec2_conn'], instance.id )
        init_lib.wait_for_available( g['ec2_conn'], volume.id )
        if not g['ec2_conn'].attach_volume( volume.id, instance.id, '/dev/sdb' ):
            raise SpinupError( "Failed to attach volume {} to instance {}".format(
                volume.id,
                instance.id
            ) )


