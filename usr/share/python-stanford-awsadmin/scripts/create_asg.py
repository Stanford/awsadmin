#!/usr/bin/python -u
#
# Copyright 2014
#         The Board of Trustees of the Leland Stanford Junior University

"""Create a specified AWS auto-scaling group

This script reads an Auto-Scaling Group's configuration from /etc/aws/aws-ami.conf file, creates a launch configuration, and an auto-scaling group. This
script will launch specified number of EC2 instances with the type
and other values defined in aws-ami.conf file.
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
    return "Create an auto-scaling group and launch instances."

def main(*args):
    """ Create an auto-scaling group and launch instances. 
    """
    # Parse command line options
    parser = argparse.ArgumentParser(description='Create ASG')
    parser.add_argument('-c', '--config_name', action="store", required=True)

    args, unknown = parser.parse_known_args()
    config_name = args.config_name

    # Read INI configuration file
    config = ConfigParser.SafeConfigParser()
    default_file = awsadmin_cfg.AWS_CONF_DIR + '/default'
    config_file = awsadmin_cfg.AWS_CONF_DIR + '/' + config_name
    if not config.read([default_file, config_file]):
        print "Configuration file %s doesn't exist" % config_file
        sys.exit(1)
    if not config.has_section(config_name):
        print "No such configuration section: %s" % config_name
        sys.exit(1)

    # Get launch configuration
    try:
        ec2_type = config.get(config_name, 'ec2_type')
        ec2_role = config.get(config_name, 'ec2_role')
        image_id = config.get(config_name, 'image_id')
        keypair = config.get(config_name, 'keypair')
        version = config.get(config_name, 'version')
        launch_config_name = config.get(config_name, 'launch_config_name')
        security_group = config.get(config_name, 'security_group')
        userdata = config.get(config_name, 'userdata')
        block_device = config.get(config_name, 'block_device')
    except ConfigParser.NoOptionError, e:
        sys_exit(1,`e`)

    try:
        elb = config.get(config_name, 'load-balancer')
    except ConfigParser.NoOptionError, e:
        elb = load_balancer = ''

    if elb:
        load_balancer = '--load-balancers ' + elb
    
    # Get ASG configuration
    try:
        auto_scaling_group_name = config.get(config_name, 'auto_scaling_group_name')
        availability_zones = config.get(config_name, 'availability_zones')
        min_size = config.get(config_name, 'min_size')
        max_size = config.get(config_name, 'max_size')
        desired_capacity = config.get(config_name, 'desired_capacity')
        tag = config.get(config_name, 'tag')
    except ConfigParser.NoOptionError, e:
        sys_exit(1,e)

    lc_cmd = ' '.join(['as-create-launch-config',launch_config_name,
                       '--image-id',image_id,'-t',ec2_type,
                       '--key',keypair,'--group',security_group,
                       '--user-data-file',userdata,
                       '--block-device-mapping',block_device,
                       '--iam-instance-profile',ec2_role])

    (status,output) = commands.getstatusoutput(lc_cmd)
    print output
    if status != 0:
        print "ERROR in creating LC" + launch_config_name
        print output
        sys.exit(1)

    asg_cmd = ' '.join(['as-create-auto-scaling-group',auto_scaling_group_name,
                        '--launch-configuration',launch_config_name,
                        '--availability-zones',availability_zones,
                        '--max-size',max_size,'--min-size',min_size,
                        load_balancer,
                        '--desired-capacity',desired_capacity,'--tag',tag])

    (status,output) = commands.getstatusoutput(asg_cmd)
    print output
    if status != 0:
        print "ERROR in creating ASG " + auto_scaling_group_name
        sys.exit(1)
    
# Only execute the code when it's called as a script, not just imported.
if __name__ == '__main__':
    main(*sys.argv[1:])
