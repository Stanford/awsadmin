#!/usr/bin/env python
#
# Copyright 2014
#         The Board of Trustees of the Leland Stanford Junior University

"""Delete a specified auto-scaling group

This script deletes an auto-scaling group. It forces the termination of 
the running instances in the group, deletes the auto-scaling group, and then
deletes the launch configuration.
                
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
    return "Delete an auto-scaling group and terminate instances in the group."

def main(*args):
    """ Delete an auto-scaling group, launch configuration and terminate
        AWS EC2 instances in the group.
    """

    # Parse command line options
    parser = argparse.ArgumentParser(description='Create ASG')
    parser.add_argument('-c', '--config_name', action="store", required=True)
    parser.add_argument('-f', '--force', action="store_true", default=False,
                        help='delete the auto-scaling group', required=True)

    args, unknown = parser.parse_known_args()
    config_name = args.config_name
    force = args.force

    # Read INI configuration file
    config = ConfigParser.SafeConfigParser()
    config_file = awsadmin_cfg.AWS_CONF_DIR + '/' + config_name
    if not config.read([config_file]):
        print "Configuration file %s doesn't exist" % config_file
        sys.exit(1)
    if not config.has_section(config_name):
        print "No such configuration section: %s" % config_name
        sys.exit(1)
   
    # Get launch configuration
    try:
        launch_config_name = config.get(config_name, 'launch_config_name')
    except ConfigParser.NoSectionError, e:
        sys_exit(1,`e`)
    except ConfigParser.NoOptionError, e:
        sys_exit(1,`e`)

    # Get ASG configuration
    try:
        auto_scaling_group_name = config.get(config_name, 'auto_scaling_group_name')
    except ConfigParser.NoOptionError, e:
        raise WrongIniFormatError(`e`)

    # Delete the auto-group without asking. 
    if not force:
        msg = """We will not delete a running auto-scaling group by default.
Please use --force to force a delete. It will terminate all
running instances, and delete auto scaling configuration."""
        print msg
        sys.exit(0)

    print "Deleting ASG... " + auto_scaling_group_name
    sys.stdout.flush()
    as_cmd = ' '.join(['aws autoscaling delete-auto-scaling-group',
                   '--auto-scaling-group-name',auto_scaling_group_name,
                   '--force-delete'])
    (status,output) = commands.getstatusoutput(as_cmd)
    if status != 0:
        print "ERROR in deleting " + auto_scaling_group_name
        print output
        sys.exit(1)
    else:
        as_cmd = ' '.join(['aws autoscaling delete-launch-configuration',
                        '--launch-configuration-name',launch_config_name])
        print "Deleting LC " + launch_config_name 
        (status,output) = commands.getstatusoutput(as_cmd)
        if status != 0:
            print "ERROR in deleting " + launch_config_name
            print output
            sys.exit(1)

    while True:
        print "Delete in progress..."
        sys.stdout.flush()
        as_cmd = ' '.join(['aws autoscaling describe-auto-scaling-groups',
                         '--auto-scaling-group-names',auto_scaling_group_name,
                         '--output text'])
        (status,output) = commands.getstatusoutput(as_cmd)
        if not output:
            break

        time.sleep(4)

    print "Auto-Scaling group %s is deleted." % (auto_scaling_group_name)
    
# Only execute the code when it's called as a script, not just imported.
if __name__ == '__main__':
    main(*sys.argv[1:])
