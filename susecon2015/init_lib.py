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
import sys
import time
from yaml_lib import yaml_attr


def read_user_data( fn ):
    """
        Given a filename, returns the file's contents in a string.
    """
    r = ''
    with open( fn ) as fh: 
        r = fh.read()
        fh.close()
    return r


def get_tags( ec, r_id ):
    """
        Takes EC2Connection object and resource ID. Returns tags associated
        with that resource.
    """
    return ec.get_all_tags(filters={ "resource-id": r_id })


def get_tag( ec, obj, tag ):
    """
        Get the value of a tag associated with the given resource object.
        Returns None if the tag is not set. Warning: EC2 tags are case-sensitive.
    """
    tags = get_tags( ec, obj.id )
    found = 0
    for t in tags:
        if t.name == tag:
            found = 1
            break
    if found:
        return t
    else:
        return None


def update_tag( obj, tag, val ):
    """
        Given an EC2 resource object, a tag and a value, updates the given tag 
        to val.
    """
    for x in range(0, 5):
        error = False
        try:
            obj.add_tag( tag, val )
        except:
            error = True
            e = sys.exc_info()[0]
            print "Huh, trying again ({})".format(e)
            time.sleep(5)
        if not error:
            print "Object {} successfully tagged.".format(obj)
            break

    return None


def init_region( r ):
    """
        Takes a region string. Connects to that region.  Returns EC2Connection
        and VPCConnection objects in a tuple.
    """
    # connect to region
    c = vpc.connect_to_region( r )
    ec = ec2.connect_to_region( r )
    return ( c, ec )


def init_vpc( c, cidr ):
    """
        Takes VPCConnection object (which is actually a connection to a
        particular region) and a CIDR block string. Looks for our VPC in that
        region.  Returns the boto.vpc.vpc.VPC object corresponding to our VPC.
        See: 
        http://boto.readthedocs.org/en/latest/ref/vpc.html#boto.vpc.vpc.VPC
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


def init_subnet( c, vpc_id, cidr ):
    """
        Takes VPCConnection object, which is actually a connection to a
        region, and a CIDR block string. Looks for our subnet in that region.
        If subnet does not exist, creates it.  Returns the subnet resource
        object on success, raises exception on failure.
    """
    # look for our VPC
    all_subnets = c.get_all_subnets()
    found = False
    our_subnet = None
    for s in all_subnets:
        if s.cidr_block == cidr:
            #print "Found subnet {}".format(cidr)
            our_subnet = s
            found = True
            break
    if not found:
        our_subnet = c.create_subnet( vpc_id, cidr )

    return our_subnet


def set_subnet_map_public_ip( ec, subnet_id ):
    """
        Takes ECConnection object and SubnetId string. Attempts to set the
        MapPublicIpOnLaunch attribute to True.
        FIXME: give credit to source
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

 
def derive_ip_address( cidr_block, delegate, final8 ):
    """
        Given a CIDR block string, a delegate number, and an integer
        representing the final 8 bits of the IP address, construct and return
        the IP address derived from this values.  For example, if cidr_block is
        10.0.0.0/16, the delegate number is 10, and the final8 is 8, the
        derived IP address will be 10.0.10.8.
    """
    result = ''
    match = re.match( r'\d+\.\d+', cidr_block )
    if match:
        result = '{}.{}.{}'.format( match.group(0), delegate, final8 )
    else:
        raise SpinupError( "{} passed to derive_ip_address() is not a CIDR block!".format(cidr_block) )

    return result        
    

def get_master_instance( ec2_conn, subnet_id ):
    """
        Given EC2Connection object and Master Subnet id, check that there is
        just one instance running in that subnet - this is the Master. Raise
        exception if the number of instances is != 0. 
        Return the Master instance object.
    """
    instances = ec2_conn.get_only_instances( filters={ "subnet-id": subnet_id } )
    if 1 > len(instances):
        raise SpinupError( "There are no instances in the master subnet" )
    if 1 < len(instances):
        raise SpinupError( "There are too many instances in the master subnet" )

    return instances[0]


def template_token_subst( buf, key, val ):
    """
        Given a string (buf), a key (e.g. '@@MASTER_IP@@') and val, replace all
        occurrences of key in buf with val. Return the new string.
    """
    targetre = re.compile( re.escape( key ) )

    return re.sub( targetre, str(val), buf )


def process_user_data( fn, vars = [] ):
    """
        Given filename of user-data file and a list of environment
        variable names, replaces @@...@@ tokens with the values of the
        environment variables.  Returns the user-data string on success
        raises exception on failure.
    """
    # Get user_data string.
    buf = read_user_data( fn )
    for e in vars:
        if not e in environ:
            raise SpinupError( "Missing environment variable {}!".format( e ) )
        buf = template_token_subst( buf, '@@'+e+'@@', environ[e] )
    return buf


def count_instances_in_subnet( ec, subnet_id ):
    """
        Given EC2Connection object and subnet ID, count number of instances
        in that subnet and return it.
    """
    instance_list = ec.get_only_instances(
        filters={ "subnet-id": subnet_id }
    )
    return len(instance_list)


def make_reservation( ec, ami_id, **kwargs ):
    """
        Given EC2Connection object, delegate number, AMI ID, as well as
        all the kwargs referred to below, make a reservation for an instance
        and return the registration object.
    """

    # extract arguments to be passed to ec.run_instances()
    our_kwargs = { 
        "key_name": kwargs['key_name'],
        "subnet_id": kwargs['subnet_id'],
        "instance_type": kwargs['instance_type'],
        "private_ip_address": kwargs['private_ip_address']
    }

    # Master or minion?
    if kwargs['master']:
        our_kwargs['user_data'] = kwargs['user_data']
    else:
        # perform token substitution in user-data string
        u = kwargs['user_data']
        u = template_token_subst( u, '@@MASTER_IP@@', kwargs['master_ip'] )
        u = template_token_subst( u, '@@DELEGATE@@', kwargs['delegate_no'] )
        u = template_token_subst( u, '@@ROLE@@', kwargs['role'] )
        u = template_token_subst( u, '@@NODE_NO@@', kwargs['node_no'] )
        our_kwargs['user_data'] = u

    # Make the reservation.
    reservation = ec.run_instances( ami_id, **our_kwargs )

    # Return the reservation object.
    return reservation


def wait_for_running( ec2_conn, instance_id ):
    """
        Given an instance id, wait for its state to change to "running".
    """
    print "Waiting for {} running state".format( instance_id )
    while True:
        instances = ec2_conn.get_only_instances( instance_ids=[ instance_id ] )
        print "Current state is {}".format( instances[0].state )
        if instances[0].state != 'running':
            print "Sleeping for 5 seconds"
            time.sleep(5)
        else:
            print "Waiting another 5 seconds for good measure"
            time.sleep(5)
            break


def wait_for_available( ec2_conn, volume_id ):
    """
        Given a volume id, wait for its state to change to "available".
    """
    print "Waiting for {} available state".format( volume_id )
    while True:
        volumes = ec2_conn.get_all_volumes( volume_ids=[ volume_id ] )
        print "Current status is {}".format( volumes[0].status )
        if volumes[0].status != 'available':
            print "Sleeping for 5 seconds"
            time.sleep(5)
        else:
            break


def wait_for_detachment( ec2_conn, v_id, i_id ):
    """
        Given a volume ID and an instance ID, wait for volume to 
        become detached.
    """
    print "Waiting for volume {} to be detached from instnace {}".format(v_id, i_id)
    while True:
        attached_vol = ec2_conn.get_all_volumes(
            filters={ 
                "volume-id": v_id,
                "attachment.instance-id": i_id,
                "attachment.device": "/dev/sdb"
            }
        )
        print "attached_vol == {}".format(attached_vol)
        if attached_vol is None or len(attached_vol) == 0:
            print "Detached!"
            break
        else:
            time.sleep(5)
            print "Still attached."

