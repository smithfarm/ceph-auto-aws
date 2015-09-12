#
# init_lib.py
#
# functions for initialization
#

from aws_lib import SpinupError
import base64
from boto import vpc, ec2
from os import environ
from pprint import pprint
from yaml_lib import yaml_attr


def read_user_data( fn ):
    r = ''
    with open( fn ) as fh: 
        r = fh.read()
        fh.close()
    return r


def init_user_data( fn ):
    """
        Takes a filename. Returns the corresponding user-data string (base64).
    """
    u = read_user_data( fn )
    return u


def init_region( r ):
    """
        Takes a region string. Connects to that region.
        Returns the VPC connection.
    """
    # connect to region
    c = vpc.connect_to_region( r )
    ec = ec2.connect_to_region( r )
    return ( c, ec )


def init_vpc( c, our_id ):
    """
        Takes VPCConnection object, which is actually a connection 
        to a particular region. Looks for our VPC in that region.
        Returns the VpcId of our VPC.
    """
    # look for our VPC
    all_vpcs = c.get_all_vpcs()
    found = 0
    our_vpc = None
    for v in all_vpcs:
        if v.id == our_id:
            our_vpc = v
            found = 1
            break
    if not found:
        raise SpinupError( "VPC {} not found".format(v.id) )

    return our_vpc


def init_subnet( c, our_id ):
    """
        Takes VPCConnection object, which is actually a connection 
        to a particular region. Looks for our subnet in that region.
        Returns the SubnetId of our subnet.
    """
    # look for our VPC
    all_subnets = c.get_all_subnets()
    found = 0
    our_subnet = None
    for s in all_subnets:
        if s.id == our_id:
            our_subnet = s
            found = 1
            break
    if not found:
        SpinupError( "Subnet {} not found".format(s.id) )

    return our_subnet


def set_subnet_map_public_ip( ec, subnet_id ):
    """
        Takes ECConnection object and SubnetId string. Attempts to set
        the MapPublicIpOnLaunch attribute to True.
    """
    orig_api_version = ec.APIVersion
    ec.APIVersion = '2014-06-15'
    ec.get_status(
        'ModifySubnetAttribute',
        {'SubnetId': subnet_id, 'MapPublicIpOnLaunch.Value': 'true'},
        verb='POST'
    )
    ec.APIVersion = orig_api_version

    return None

