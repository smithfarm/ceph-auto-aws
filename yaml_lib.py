#
# yaml_lib.py
#
# functions for parsing aws.yaml
#

from aws_lib import SpinupError
import yaml


def yaml_attr( node, name, default ):
    """Takes three arguments: node in yaml structure, attr name, and default
       If default is None, checks that attr exists in node.
       If default is not None, returns attr value if attr exists and is not None,
       otherwise returns default."""
    if not ( name in node ):
        raise SpinupError( "Attribute ->{}<- missing in yaml node".format( name ) )
    if default == None and node[name] == None:
        raise SpinupError( "Required yaml attribute ->{}<- has no value".format( name ) )
    r = ''
    r = node[name] if name in node else default
    r = node[name] if node[name] != None else default
    #print "Using {} ->{}<-".format( name, r )
    return r
        

def parse_yaml(yaml_file):
    """
        Takes full path of aws.yaml file. Parses aws.yaml file. Returns a dictionary.
    """
    try:
        f = open( yaml_file )
    except OSError as e:
        raise SpinupError( "Could not read yaml file ->{}<-".format( yaml_file ) )
    conf = yaml.safe_load( f )
    f.close()

    return conf


def initialize_vpc( init ):
    """
        Takes init section of yaml structure. Connects to VPC.
        Returns the VPC connection.
    """
    init['region'] = yaml_attr( init, 'region', 'eu-west-1' )
    c = vpc.connect_to_region(init['region'])
    init['vpc'] = yaml_attr( init, 'vpc', None )
    init['vpc']['id'] = yaml_attr( init['vpc'], 'id', None )
    all_vpcs = c.get_all_vpcs()
    print all_vpcs

    return c

