#!/usr/bin/env python
#
# Copyright 2014
#         The Board of Trustees of the Leland Stanford Junior University

"""Update specified auto-scaling group's launch configuration. 

This script reads auto-scaling group's configuration from 
/etc/aws/aws/aws-ami.conf file, creates a new launch configuration and 
updates the auto-scaling group to use the configuration for new EC2 
instances going forward. 

Optionally, you can pass in ec2 type to change EC2's instance type. All
other launch configurations will be the same as those in aws-ami.conf
file. It can be used for temporary test. If you want to make it
permanent, change the aws-ami.conf instead. A temporary launch 
configuration will be created which you can delete later if it is no
longer in use.
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
    return "Create new launch configuration and update an auto-scaling group."

def lc_exist(config_name):
    """ Check if a launch config exists 
    """

    m = re.compile(config_name)
    lc_cmd = ' '.join(['as-describe-launch-configs',config_name])
    (status,output) = commands.getstatusoutput(lc_cmd)
    return  m.search(output)

def main(*args):
    """ Create new launch configuration and update an auto-scaling group's 
        configuration.
    """

    # Parse command line options
    parser = argparse.ArgumentParser(description='Update launch configuration')
    parser.add_argument('-c', '--config_name', action="store", required=True)
    parser.add_argument('-t', '--ec2-type', action="store", required=False,
                        help='An ec2 type. If given, override the default configuration. Useful for testing.')

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

    if args.ec2_type:
        ec2_type = args.ec2_type
    else:
       ec2_type = config.get(config_name, 'ec2_type')
   
    # Generate a new lc file
    launch_config_name = "%s_%s_%s" % (config_name,ec2_type,(time.strftime("%Y-%m-%d-%H%M")))

    try:
        launch_config_name = config.get(config_name, 'launch_config_name')
        ec2_role = config.get(config_name, 'ec2_role')
        image_id = config.get(config_name, 'image_id')
        keypair = config.get(config_name, 'keypair')
        security_group = config.get(config_name, 'security_group')
        userdata = config.get(config_name, 'userdata')
        block_device = config.get(config_name, 'block_device')
        auto_scaling_group_name = config.get(config_name, 'auto_scaling_group_name')
    except ConfigParser.NoSectionError, e:
        sys_exit(1,`e`)

    if lc_exist(launch_config_name):
        print "Launch configuration exists: " + launch_config_name
        sys.exit(1)
    else:
        lc_cmd = ' '.join(['as-create-launch-config',launch_config_name,
                       '--image-id',image_id,'-t',ec2_type,
                       '--key',keypair,'--group',security_group,
                       '--user-data-file',userdata,
                       '--block-device-mapping',block_device,
                       '--iam-instance-profile',ec2_role])

        (status,output) = commands.getstatusoutput(lc_cmd)

        if status != 0:
            print "ERROR in creating LC " + launch_config_name
            print output
            sys.exit(1)

    # Update ASG with the existing or new LC created above.
    lc_cmd = ' '.join(['as-update-auto-scaling-group',
                            auto_scaling_group_name,
                            '--launch-configuration',launch_config_name])

    (status,output) = commands.getstatusoutput(lc_cmd)
    if status != 0:
        print "ERROR in updating ASG" + launch_config_name + output
        sys.exit(1)
    else:
        lc_cmd = ' '.join(['as-describe-launch-configs', launch_config_name])
        (status,output) = commands.getstatusoutput(lc_cmd)
        print output

    sys.exit(0)

# Only execute the code when it's called as a script, not just imported.
if __name__ == '__main__':
    main(*sys.argv[1:])
