#!/usr/bin/env python
#
# Copyright 2014
#     The Board of Trustees of the Leland Stanford Junior University

"""Manage vpc and subnet configurations.
"""

__author__ = 'sfeng@stanford.edu'

import sys
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
from lib.Utils import config_option

def short_desc():
    return "Setup, display, or delete VPC."

def build_vpc(config_name,config):
    """ Build VPC based on the configuration file.
    """
    cidr_block = config.get(config_name, 'vpc_network')
    aws_cmd = ' '.join(['aws ec2 create-vpc --cidr-block', cidr_block])
    return commands.getstatusoutput(aws_cmd)
    
def remove_vpc(config_name,config):
    """ Delete VPC by vpcid
    """
    aws_cmd = ' '.join(['aws ec2' ,config_name,'-f'])
    print "Deleting LC " + config_name
    return commands.getstatusoutput(as_cmd)

def show_vpc(config_name,config):
    """ Describe VPC 
    """
    vpcid   = config.get(config_name, 'vpcid')
    aws_cmd = ' '.join(['aws ec2 describe-vpcs','--vpc-id', vpcid])
    return commands.getstatusoutput(aws_cmd)

def main(*args):

    # Parse command line options
    parser = argparse.ArgumentParser(description='VPC admin')
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('-c', '--config_name', action="store", required=True)
    group.add_argument('-b', '--buildvpc', action="store_true", default=False,
                       help='Build VPC')
    group.add_argument('-r', '--removevpc', action="store_true", 
                        default=False, help='Remove VPC')
    group.add_argument('-s','--showvpc', action="store_true", 
                        default=False, help='Show VPC configuration')

    args = parser.parse_args()
   
    # Read INI configuration file
    config = ConfigParser.SafeConfigParser()
    config_file = awsadmin_cfg.AMI_CONF_DIR + '/' + args.config_name
    if not config.read(config_file):
        print "Configuration file %s doesn't exist" % config_file
        sys.exit(1)
    if not config.has_section(args.config_name):
        print "No such configuration section: %s" % args.config_name
        sys.exit(1)

    if args.showvpc: 
        (status,output) = show_vpc(args.config_name,config)
    elif args.buildvpc:
        (status,output) = build_vpc(args.config_name,config)
    elif args.removevpc:
        (status,output) = remove_vpc(args.config_name,config)

    if status != 0:
        print "ERROR in operation on " + args.config_name
        sys.exit(1)
    else:
        print output

if __name__ == '__main__':
    main(*sys.argv[1:])
