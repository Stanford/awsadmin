#!/usr/bin/env python
#
# Copyright 2014
#     The Board of Trustees of the Leland Stanford Junior University

"""Manage subnet configurations.
"""

__author__ = 'sfeng@stanford.edu'

import argparse
import sys
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
from lib.Utils import config_option

def short_desc():
    return "Setup, display, or delete VPC subnets."

def build(config_name,config):
    """ Build VPC based on the configuration file.
    """
    vpcid   = config.get(config_name, 'vpcid')
    (s1,s2,s3) = config.get(config_name,'elb_subnets').replace(' ','').split(',')
    for s in (s1,s2,s3):
        (zone,cidr_block) = s.split(':')
        aws_cmd = ' '.join(['aws ec2 create-subnet', '--vpc-id', vpcid,
                          '--cidr-block', cidr_block,
                          '--availability-zone', zone])
        (status,output) = commands.getstatusoutput(aws_cmd)
        if status != 0:
            print "ERROR:" + output
            sys.exit(1)

    return (0, 'okay')

def remove(config_name,config):
    """ Delete VPC by vpcid
    """
    #aws_cmd = ' '.join(['aws ec2 ,config_name, '-f'])
    print "Deleting LC " + config_name
    return commands.getstatusoutput(as_cmd)

def show(config_name,config):
    """ Describe VPC subnet
    """
    vpcid   = config.get(config_name, 'vpcid')
    filters = 'Name=vpc-id,Values=' + vpcid
    aws_cmd = ' '.join(['aws ec2 describe-subnets',
                        '--filters', filters])
    return commands.getstatusoutput(aws_cmd)

def main(*args):

    # Parse command line options
    parser = argparse.ArgumentParser(description='VPC subnet admin')
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('-c', '--config_name', action="store", required=True)
    group.add_argument('-b', '--build', action="store_true", 
                        default=False, help='Build VPC')
    group.add_argument('-r', '--remove', action="store_true", 
                        default=False, help='Remove VPC')
    group.add_argument('-s','--show', action="store_true", 
                        default=False, help='Show VPC configuration')
    group.add_argument('-t','--type', action="store", help='subnet type')

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

    if args.show: 
        (status,output) = show(args.config_name,config)
    elif args.build:
        (status, output) = build(args.config_name,config)
    elif args.remove:
        (status,output) = remove(args.config_name,config)

    if status != 0:
        print "ERROR in operation on " + args.config_name
        sys.exit(1)
    else:
        print output

if __name__ == '__main__':
    main(*sys.argv[1:])
