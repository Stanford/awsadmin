#!/usr/bin/env python
#
# Copyright 2014
#         The Board of Trustees of the Leland Stanford Junior University

"""Double desired capacity in an auto-scaling group 

This script doubles the capacity of an auto-scaling group.

Options:
         -c, --config_name=<value>
           An INI section in /etc/aws/aws-ami.conf file which contains
           values needed to launch the instance
         -h / --help
            Print this message and exit
                
"""

__author__ = 'sfeng@stanford.edu'

import re
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
import ConfigParser
from lib.Utils import sys_exit

def short_desc():
    return "Double the capacity of an auto-scaling group."

def main(*args):
    """ Double the capacity of an auto-scaling group.
    """
    # Parse command line options
    try:
        opts, args = getopt.getopt(args, 'hc:', ['help', 'config-name='] )
    except getopt.error, msg:
        sys_exit(1, msg)

    config_name=''
    # Process options
    for option, arg in opts:
        if option in ('-c', '--config_name'):
            config_name=(arg)
        elif option in ('-h', '--help'):
            sys_exit(0,__doc__)

    if not config_name:
        sys_exit(1,"Configuration name is required")

    # Read INI configuration file
    config = ConfigParser.ConfigParser()
    try:
        config.read(awsadmin_cfg.AMI_CONF_INI)
    except AttributeError, e:
        sys_exit(1,e)
   
    # Get launch configuration
    try:
        ec2_type = config.get(config_name, 'ec2_type')
    except ConfigParser.NoSectionError, e:
        sys_exit(1,`e`)

    # Get ASG configuration
    try:
        auto_scaling_group_name = config.get(config_name, 'auto_scaling_group_name')
        desired_capacity = config.get(config_name, 'desired_capacity')
    except ConfigParser.NoOptionError, e:
        sys_exit(1,e)

    # Scale out to keep service capacity while we recycle instances
    double_capacity = str(int(desired_capacity) * 2)
    set_capacity_cmd = ' '.join(['as-set-desired-capacity',
                                  auto_scaling_group_name,
                                  '--desired-capacity',double_capacity])

    (status,output) = commands.getstatusoutput(set_capacity_cmd)
    print output
    status = 0 
    if status != 0:
        print "ERROR in doubling capacity for " + auto_scaling_group_name
        print output
        sys.exit(1)
    
# Only execute the code when it's called as a script, not just imported.
if __name__ == '__main__':
    main(*sys.argv[1:])
