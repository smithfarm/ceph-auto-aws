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


def write_yaml( y, fn ):
    """
        Takes YaML data structure and filename. Writes/updates the file.
    """
    try:
        f = open( fn, 'w')
    except OSError as e:
        raise SpinupError( "Could not open yaml file ->{}<- for writing".format(fn) )
    f.write( yaml.safe_dump(y, default_flow_style=False) )
    return None


