#!/usr/bin/python -u
#
# Copyright 2014
#         The Board of Trustees of the Leland Stanford Junior University

"""Create a new ec2 instance and put it in its own auto-scaling group

This script creates a new ec2 instance AWS. An auto-scaling group with capacity 1 is also created.
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
    return "Create an AMI from an instance."

def main(*args):
    """ Create AWS AMI image
    """
    # Parse command line options
    parser = argparse.ArgumentParser(description='Create AWS AMI')
    parser.add_argument('-c', '--config_name', action="store", required=True)
    parser.add_argument('-i', '--instance_id', action="store", required=True)
    parser.add_argument('-r', '--reboot', action="store_true", default=False,
                        help="Reboot before making image, default is no reboot")

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

    instance_id = args.instance_id
    reboot = '--no-reboot'
    if args.reboot:
        reboot = '--reboot'

    # Get launch configuration
    try:
        ec2_type = config.get(config_name, 'ec2_type')
    except ConfigParser.NoSectionError, e:
        sys_exit(1,`e`)

    # Get ASG configuration
    ami_name = "%s-%s-%s" % (config_name,(time.strftime("%Y-%m-%d-%H%M")),'amd64')
    lc_cmd = ' '.join(['aws ec2 create-image --instance-id',instance_id,
                      '--name',ami_name,reboot])
    
    (status,output) = commands.getstatusoutput(lc_cmd)
    if status != 0:
        print "ERROR in creating AMI for " + instance_id
        print output
        sys.exit(1)
    else:
        image_id = json.loads(output)['ImageId']
        print "Creating image %s..." % (image_id)
        sys.stdout.flush()
    
    # Wait for the image to be available
    aws_cmd = ' '.join(['aws ec2 describe-images --image-id',image_id])
    while True:
        (status,output) = commands.getstatusoutput(aws_cmd)
        state = json.loads(output)['Images'][0]['State']
        print state
        sys.stdout.flush()
        if state == 'available':
             break
        else:
            time.sleep(5)

    print "Image %s is available." % (image_id)
    sys.exit(0)
    
# Only execute the code when it's called as a script, not just imported.
if __name__ == '__main__':
    main(*sys.argv[1:])
