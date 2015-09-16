#!/usr/bin/python
#
# aws.py
#
# Spin up Ceph cluster in AWS.
#
# Cluster is defined in the aws.yaml file.
#
# Generate pseudo-code from #PC comments:
#   $ grep -E '^ *#PC' aws.py | sed -e 's/#PC //'g   
#

import argparse
from aws_lib import SpinupError
import init_lib
from pprint import pprint
import sys
import yaml_lib

#PC * Parse arguments.
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
#parser.add_argument( 
#    'operation', 
#    default='create', 
#    help="cluster-wide cloud operation ('create', 'terminate', 'pause', "+
#         "'resume', 'start', 'stop', 'suspend', 'unpause') to perform",
#    nargs='?' 
#)
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

#PC * Clobber existing VPC tag with YAML value ("vpc" -> "name").
init_lib.update_tag( g['vpc_obj'], 'Name', n['name'] )
print "Found VPC {} (Name: {})".format(n['cidr-block'], n['name'])

#PC * Look at YAML "subnets" and see how many there are.
subnets = yaml_lib.yaml_attr( y, 'subnets', None )
print "{} subnets in yaml".format(len(subnets))

#PC * Raise exception if there is not at least one subnet.
if 1 > len(n):
    raise SpinupError( "No subnets in yaml" )

#PC * Loop through the YAML subnet definitions. All subnets are assumed to
#PC   exist in the VPC. If they don't, bad things happen.
g['subnet_obj'] = []
count = 0
for s in subnets:
    #PC * First subnet is assumed to be the "Master Subnet" (CIDR block
    #PC   defaults to 10.0.0.0/24).
    if count == 0:
        # master subnet
        s['name'] = yaml_lib.yaml_attr( s, 'name', 'master' )
        s['cidr-block'] = yaml_lib.yaml_attr( s, 'cidr-block', '10.0.0.0/24' )
        print "Looking for master subnet {} ({})".format(s['cidr-block'], s['name'])
    #PC * All others are "Minion Subnets" (i.e. for delegates): CIDR block
    #PC   defaults to 10.0.<delegate>.0/24
    else:
        # minion subnet
        s['name'] = yaml_lib.yaml_attr( s, 'name', None )
        s['cidr-block'] = yaml_lib.yaml_attr( s, 'cidr-block', '10.0.{}.0/24'.format(count) )
        print "Looking for minion subnet {} ({})".format(s['cidr-block'], s['name'])
    #PC * For each subnet (Master or Minion) in YAML: 
    #PC     * Get subnet object and store it.
    g['subnet_obj'].append( init_lib.init_subnet( g['vpc_conn'], s['cidr-block'] ) )
    #PC     * Clobber existing subnet tag with the one specified in YAML.
    init_lib.update_tag( g['subnet_obj'][count], 'Name', s['name'] )
    #PC     * Update subnet "MapPublicIpOnLaunch" attribute, so all instances
    #PC       created in this subnet will automatically get a public IP address.
    if g['subnet_obj'][count].mapPublicIpOnLaunch == 'false':
        init_lib.set_subnet_map_public_ip( g['ec2_conn'], g['subnet_obj'][count].id )
    print "Found subnet {} ({})".format(s['cidr-block'], s['name'])
    count += 1

#PC * If --master option was given on the command line: 
if args.master:

    #PC * Get all existing instances in the subnet.
    subnet_id = g['subnet_obj'][0].id
    subnet_cidr = g['subnet_obj'][0].cidr_block
    noofinstances = init_lib.count_instances_in_subnet(
        g['ec2_conn'],
        subnet_id
    )

    #PC * If there are already instances in the subnet, print their IDs and bail out.
    if noofinstances > 0:
        print "There are already {} instances in the Master subnet {}".format(noofinstances, subnet_cidr)
        sys.exit(1)

    print "Creating 1 master node in the Master Subnet {}.".format( y['subnets'][0]['cidr-block'] )

    #PC * Process Master user-data script (replace tokens with values from environment)
    u = init_lib.process_user_data( 
        y['master']['user-data'], 
        y['master']['replace-from-environment'] 
    )
    
    #PC * Derive address (e.g. 10.0.0.10) for the Master
    g['master']['ip-address'] = init_lib.derive_ip_address( 
        y['subnets'][0]['cidr-block'],
        0,
        10
    )

    #PC * Spin up AWS instance for the Master.
    reservation = init_lib.make_reservation( 
        g['ec2_conn'], 
        y['master']['ami-id'],
        key_name=y['keyname'],
        instance_type=y['master']['type'],
        user_data=u,
        subnet_id=g['subnet_obj'][0].id,
        private_ip_address=y['master']['ip-address'],
        master=True
    )
    g['master_instance'] = reservation.instances[0]

    #PC * Clobber tag with hard-coded value "master".
    init_lib.update_tag( g['master_instance'], 'Name', 'master' )

    #PC * Report result to user, and exit.
    print "Master node {} ({}, {}) created.".format(
        g['master_instance'].id, 
        g['master_instance'].ip_address,
        g['master_instance'].private_ip_address
    )
    sys.exit(0)

#PC * --master option was *not* given on the command line. Script continues.
#PC * Check that master exists and get its public IP address. Continue if and
#PC   only if there is a single instance in the Master Subnet.
# FIXME: check that the Master instance state is "running".
g['master_instance'] = init_lib.get_master_instance( 
    g['ec2_conn'], 
    g['subnet_obj'][0].id 
)

#PC * Clobber Master instance tag with hard-coded value "master".
init_lib.update_tag( g['master_instance'], 'Name', 'master' )
print "Found master instance {} ({}, {})".format( 
    g['master_instance'].id, 
    g['master_instance'].ip_address,
    g['master_instance'].private_ip_address
)

#PC * The YAML should contain "install_subnets" which is a list of delegate
#PC   numbers. Look at how many elements are in that list. This is the number
#PC   of subnets that we will be installing.
y['install_subnets'] = yaml_lib.yaml_attr( y, 'install_subnets', None )
n = len(y['install_subnets'])
print "Installing {} of {} subnet(s)".format(n, len(subnets))

#PC * Conduct sanity checks on "install_subnets" list:
for n in y['install_subnets']:
    #PC * Delegate numbers cannot be negative.
    if n < 0:
        raise SpinupError( "No negative subnets, silly" )
    #PC * Delegate number 0 is not allowed (use --master).
    if n == 0:
        raise SpinupError( "Use --master to install the master subnet 10.0.0.0/24" )
    #PC * The total number of delegates should be equal to the number of subnets plus one.
    #PC   If any delegate number exceeds this value, raise an exception.
    if n > len(subnets) + 1:
        raise SpinupError( "Subnet {} is to be installed, but only {} subnets are defined in yaml".format(n, len(subnets)) )

#PC * Initialize structures to hold the cluster node resource objects.
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
    
#PC * Loop over the delegate numbers in "install_subnets":
for delegate in y['install_subnets']:

    #PC * Store subnet ID and CIDR block in temporary variables
    subnet_id = g['subnet_obj'][delegate].id
    subnet_cidr = g['subnet_obj'][delegate].cidr_block
    print "Installing subnet {} ({})".format( subnet_cidr, subnet_id )

    #PC * Get all existing instances in the subnet.
    noofinstances = init_lib.count_instances_in_subnet(
        g['ec2_conn'],
        subnet_id
    )

    #PC * If there are already instances in the subnet, print their IDs and bail out.
    if noofinstances > 0:
        print "There are already {} instances in subnet {}".format(noofinstances, subnet_cidr)
        sys.exit(1)

    #PC * Create 1 admin node:
    print "Create 1 admin node"

    #PC     * Derive IP address of admin node
    g['admin_node'][delegate]['ip-address'] = init_lib.derive_ip_address( 
        y['subnets'][0]['cidr-block'],
        delegate,
        10
    )

    #PC     * Process admin node user-data
    u = init_lib.process_user_data( 
        y['admin']['user-data'], 
        y['admin']['replace-from-environment']
    )

    #PC     * Spin up admin node instance
    reservation = init_lib.make_reservation( 
        g['ec2_conn'], 
        y['admin']['ami-id'],
        key_name=y['keyname'],
        instance_type=y['admin']['type'],
        user_data=u,
        subnet_id=subnet_id,
        private_ip_address=g['admin_node'][delegate]['ip-address'],
        master=False,
        master_ip=g['master_instance'].private_ip_address,
        delegate_no=delegate
    )
    g['admin_node'][delegate]['instance'] = reservation.instances[0]

    #PC     * Set admin node tag to "admin".
    init_lib.update_tag( g['admin_node'][delegate]['instance'], 'Name', 'admin' )

    #PC     * Set admin node "Delegate" tag to the delegate number.
    init_lib.update_tag( g['admin_node'][delegate]['instance'], 'Delegate', delegate )

    #PC * Create 3 mon nodes.
    print "Create 3 mon nodes"

    #PC     * Process mon node user-data
    u = init_lib.process_user_data( 
        y['mon']['user-data'], 
        y['mon']['replace-from-environment'] 
    )

    #PC     * For each of the three mon nodes:
    for x in range(1, 4):

        mon_node = g['mon{}_node'.format(x)][delegate]

        #PC     * Derive IP address
        mon_node['ip-address'] = init_lib.derive_ip_address( 
            y['subnets'][0]['cidr-block'],
            delegate,
            10+x
        )

        #PC     * Make reservation.
        reservation = init_lib.make_reservation( 
            g['ec2_conn'], 
            y['mon']['ami-id'],
            key_name=y['keyname'],
            instance_type=y['mon']['type'],
            user_data=u,
            subnet_id=subnet_id,
            private_ip_address=mon_node['ip-address'],
            master=False,
            master_ip=g['master_instance'].private_ip_address,
            delegate_no=delegate
        )
        mon_node['instance'] = reservation.instances[0]

        #PC     * Update tags.
        init_lib.update_tag( mon_node['instance'], 'Name', 'mon' )
        init_lib.update_tag( mon_node['instance'], 'Delegate', delegate )

        #PC     * Create OSD volume.
        mon_node['volume'] = g['ec2_conn'].create_volume( volume_size, mon_node['instance'].placement )

    for x in range(1, 4):

        mon_node = g['mon{}_node'.format(x)][delegate]
        instance = mon_node['instance']
        volume = mon_node['volume']

        #PC     * Make sure node state is "running" (wait if necessary).
        init_lib.wait_for_running( g['ec2_conn'], instance.id )

        #PC     * Make sure volume status is "available" (wait if necessary).
        init_lib.wait_for_available( g['ec2_conn'], volume.id )

        #PC     * Attach the OSD volume to the mon node.
        if not g['ec2_conn'].attach_volume( volume.id, instance.id, '/dev/sdb' ):
            raise SpinupError( "Failed to attach volume {} to instance {}".format(
                volume.id,
                instance.id
            ) )

