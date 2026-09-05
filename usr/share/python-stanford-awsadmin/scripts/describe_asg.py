#!/usr/bin/env python
#
# Copyright 2014
#         The Board of Trustees of the Leland Stanford Junior University

"""Describe an auto-scaling group configuration.
"""

__author__ = 'sfeng@stanford.edu'

import sys
import getopt
import time
import string
import random
import re
import commands
import json

import paths
import awsadmin_cfg
import argparse
import ConfigParser
from lib.Utils import sys_exit

def short_desc():
    return "Describes the specified Auto Scaling groups."

def my_print(data):
    """ Print ASG information
    """
    asg_data = json.loads(data)
    groups =  asg_data["AutoScalingGroups"]
    for group in groups:
        for k,v in group.items():
            if k not in ('Instances','Tags'):
                print '{0:23s}: {1:20s}'.format(str(k),str(v)).replace("u'","'")
    print
    for list in ('Instances','Tags'):
        for l in group[list]:
            for k,v in l.items():
                print '{0:23s}: {1:20s}'.format(str(k), str(v))
            print

def main(*args):
    """ Describe auto-scaling group
    """
    # Parse command line options
    parser = argparse.ArgumentParser(description='Describe AWS ASG')
    parser.add_argument('-c', '--config_name', action="store", required=True)

    args, unknown = parser.parse_known_args()
    config_name = args.config_name

    # Read INI configuration file
    config = ConfigParser.SafeConfigParser()
    config_file = awsadmin_cfg.AWS_CONF_DIR + '/' + config_name
    if not config.read([config_file]):
        print "Configuration file %s doesn't exist" % config_file
        sys.exit(1)
    if not config.has_section(config_name):
        print "No such configuration section: %s" % config_name
        sys.exit(1)

    try:
        auto_scaling_group_name = config.get(config_name, 'auto_scaling_group_name')
    except ConfigParser.NoOptionError, e:
        sys_exit(1,`e`)
    as_cmd = ' '.join(['aws autoscaling describe-auto-scaling-groups',
                     '--auto-scaling-group-names',auto_scaling_group_name,
                     '--output json'])

    (status,output) = commands.getstatusoutput(as_cmd)
    if status != 0:
        print "ERROR in verifing ASG"
        sys.exit(1)

    if json.loads(output)["AutoScalingGroups"]:
        my_print(output)
    else:
        print "No such a group."

    sys.exit(0)
    
# Only execute the code when it's called as a script, not just imported.
if __name__ == '__main__':
    main(*sys.argv[1:])
