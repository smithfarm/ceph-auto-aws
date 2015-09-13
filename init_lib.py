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
import re
from yaml_lib import yaml_attr


def read_user_data( fn ):
    r = ''
    with open( fn ) as fh: 
        r = fh.read()
        fh.close()
    return r


def get_tags( ec, r_id ):
    """
        Takes EC2Connection object and resource ID. Returns
        tags associated with that resource.
    """
    return ec.get_all_tags(filters={ "resource-id": r_id })


def get_name( ec, obj ):
    tags = get_tags( ec, obj.id )
    found = 0
    for t in tags:
        if t.name.lower() == 'name':
            found = 1
            break
    if found:
        return t
    else:
        return None


def update_name( obj, val ):
    """
        Given an EC2 resource object and a value, updates
        the "name" tag of the resource to val.
    """
    obj.add_tag( 'Name', val )
    return None


def init_region( r ):
    """
        Takes a region string. Connects to that region.
        Returns the VPC connection.
    """
    # connect to region
    c = vpc.connect_to_region( r )
    ec = ec2.connect_to_region( r )
    return ( c, ec )


def init_vpc( c, cidr ):
    """
        Takes VPCConnection object (which is actually a connection 
        to a particular region) and a CIDR block string. Looks for our VPC in that region.
        Returns the VpcId of our VPC.
    """
    # look for our VPC
    all_vpcs = c.get_all_vpcs()
    found = 0
    our_vpc = None
    for v in all_vpcs:
        if v.cidr_block == cidr:
            our_vpc = v
            found = 1
            break
    if not found:
        raise SpinupError( "VPC {} not found".format(cidr) )

    return our_vpc


def init_subnet( c, cidr ):
    """
        Takes VPCConnection object, which is actually a connection to 
        a particular region, and a CIDR block string. Looks for our 
        subnet in that region.  Returns the subnet resource object.
    """
    # look for our VPC
    all_subnets = c.get_all_subnets()
    found = 0
    our_subnet = None
    for s in all_subnets:
        if s.cidr_block == cidr:
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


def template_token_subst( buf, key, val ):
    """
        Given a string (buf), a key (e.g. '@@MASTER_IP@@') and val
        (e.g. 10.0.1.34), replace all occurrences of key in buf with
        val. Return the new string.
    """
    targetre = re.compile( re.escape( key ) )
    return re.sub( targetre, val, buf )


def make_reservation( ec, ami_id, **kwargs ):
    """
        Given EC2Connection object, AMI ID, and kwargs with key_name,
        instance_type, user_data, and subnet_id, call run_instances 
        and return the reservation object.
    """
    # get user_data string
    u = read_user_data( kwargs['user_data'] )
    if not kwargs['master']:
        u = template_token_subst( u, '@@MASTER_IP@@', kwargs['master_ip'] )
        u = template_token_subst( u, '@@DELEGATE@@', str(kwargs['delegate']) )
    # get reservation
    reservation = ec.run_instances( 
        ami_id,
        key_name=kwargs['key_name'],
        instance_type=kwargs['instance_type'],
        user_data=u,
        subnet_id=kwargs['subnet_id']
    )
    # return the instance object
    return reservation.instances[0]


