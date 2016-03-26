#!/usr/bin/python
#
# list_public_ips.py
#
# Print public IP addresses of admin nodes of all Delegates.
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

def fetch_public_ip( ec2_conn, subnet_id, tag_value ):
    instances = ec2_conn.get_only_instances( 
        filters={ "subnet-id": subnet_id, "tag-key": "Role", "tag-value": tag_value } 
    )
    found = False
    public_ip = ''
    for i in instances:
        public_ip = "{}".format(i.ip_address)
        found = True
    if not found:
        public_ip = "(none)"
    return public_ip

parser = argparse.ArgumentParser( description='Get public IP addresses of Delegate admin nodes.' )
parser.add_argument( 
    '--yaml', 
    default='./aws.yaml', 
    help="yaml file to read (defaults to ./aws.yaml)" 
)
args = parser.parse_args()

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
try:
    g['vpc_obj'] = init_lib.init_vpc( g['vpc_conn'], n['cidr-block'] )
except SpinupError as e:
    print "{}".format( e )
    sys.exit()

#PC * Get Salt Master subnet (first one in "subnets" list).
#PC * If there are no subnets, print a nice message and exit.
try:
    g['master_subnet'] = init_lib.init_subnet( 
        g['vpc_conn'],
        g['vpc_obj'].id,
        y['subnets'][0]['cidr-block']
    )
except SpinupError as e:
    print "{}".format( e )
    sys.exit()

#PC * Get Salt Master instance (i.e., the sole instance in the Salt Master subnet).
try:
    g['master_instance'] = init_lib.get_master_instance( 
        g['ec2_conn'], 
        g['master_subnet'].id 
    )
except SpinupError as e:
    print "{}".format( e )
    sys.exit()
print "Salt Master is {}".format( g['master_instance'].ip_address )

#PC * Loop over all possible subnets
upper = 41
print "Looping over delegates 1-{}".format(upper-1)
for delegate in range(1, upper):

    cidr_block = '10.0.{}.0/24'.format(delegate)

    #PC * Get subnet object (raise exception if it doesn't exist).
    g['subnet_obj'] = init_lib.init_subnet( g['vpc_conn'], g['vpc_obj'].id, cidr_block )

    #PC * Get public IP addresses of admin node and windows client node
    admin_ip = fetch_public_ip( g['ec2_conn'], g['subnet_obj'].id, 'admin' )
    windows_ip = fetch_public_ip( g['ec2_conn'], g['subnet_obj'].id, 'windows' )

    #PC * Print line for the current delegate
    print "Delegate {}: admin {}, windows {}".format(delegate, admin_ip, windows_ip)
    
print "Done."
