#!/usr/bin/python
#
# admin_nodes.py
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

#PC * This script (admin_nodes.py) makes the following assumptions:
#PC     * delegate number provided in argument is really the one you want to
#PC       wipe out
#PC     * each delegate is segregated into his or her own subnet in the YAML
#PC     * these delegate subnets defined in the YAML take the form
#PC       10.0.[d].0/24, where [d] is the delegate number, and these subnets
#PC       really exist
#PC     * aws.yaml present in current directory or --yaml option provided;
#PC     * Salt Master exists and is alone in subnet 10.0.0.0/24
#PC     * SSH private key enabling SSH to Salt Master as user ec2-user is
#PC       present in $HOME/.ssh/ec2
#PC * If the above assumptions are fulfilled, the script should work.
#PC * The following is a high-level description of what the script does.
#PC * Parse command-line arguments.
parser = argparse.ArgumentParser( description='Get public IP addresses of Delegate admin nodes.' )
parser.add_argument( 
    '--yaml', 
    default='./aws.yaml', 
    help="yaml file to read (defaults to ./aws.yaml)" 
)
#parser.add_argument( 
#    'delegate', 
#    help="Delegate number to wipe out",
#    nargs='?' 
#)
args = parser.parse_args()

## Verify that delegate number was given on command line and that it is an integer.
#if args.delegate is None:
#    raise SpinupError( "Must provide delegate number to wipe out" )
#delegate = int(args.delegate)

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
