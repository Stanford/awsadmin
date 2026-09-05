#!/usr/bin/env python
#
# Copyright 2014
#         The Board of Trustees of the Leland Stanford Junior University

"""Replace all instances in an auto-scaling group with new instances

This script replaces all instances in an auto-scaling group with new
instances. To make sure no outage, the script deregister old instance from
elb, kill it, one at a time. The auto-scaling policy will create a 
new one when old one is killed, with the latest launch configuration.

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
    return "Replace all instances in an auto-scaling group with new instances."

def main(*args):
    """ Recycle all EC2 instances in auto-scaling group
    """
    # Parse command line options
    try:
        opts, args = getopt.getopt(args, 'hc:', ['help', 'config_name='] )
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
        elb = config.get(config_name, 'load-balancer')
    except ConfigParser.NoOptionError, e:
        sys_exit(1,e)

    # List all current instances running behind elb
    lb_cmd = ' '.join(['aws elb describe-instance-health',
                         '--load-balancer',elb])
    (status,output) = commands.getstatusoutput(lb_cmd)
    instance_pat = re.compile('i-\w+')
    if status != 0:
        print "ERROR in getting instances from elb " + elb
        print output
    else:
       old_instances = instance_pat.findall(output)     

    # Make sure all instances are healthy from the ELB's end
    healthy_pat = 'InService'
    for inst in old_instances:
        print "Deregister and terminate old instance " + inst
        lb_cmd = ' '.join(['aws elb deregister-instances-from-load-balancer',
                       '--load-balancer',elb,
                       '--instances', inst])
        (status,output) = commands.getstatusoutput(lb_cmd)
        while True:
            (status,output) = commands.getstatusoutput(lb_cmd)
            healthy_instances = instance_pat.findall(output)     
            if len(healthy_instances) == int(desired_capacity):
                break
            else:
                time.sleep(5)
                print "Waiting for instances healthy status..."

    # List all current instances running behind elb
    lb_cmd = ' '.join(['aws elb describe-instance-health',
                         '--load-balancer',elb])
    (status,output) = commands.getstatusoutput(lb_cmd)
    print output
    sys.exit(0)
    
# Only execute the code when it's called as a script, not just imported.
if __name__ == '__main__':
    main(*sys.argv[1:])
