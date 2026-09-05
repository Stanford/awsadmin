#!/usr/bin/python -u
#
# Copyright 2014
#         The Board of Trustees of the Leland Stanford Junior University

"""Replace all instances in an auto-scaling group with new instances

This script replaces all instances in an auto-scaling group with new
instances. To make sure no outage, the script first doubles the capacity
of the auto-scaling group, waits until all new instances are in service,
then resets the capacity to the original setting.

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
import argparse
import ConfigParser
from lib.Utils import sys_exit

def short_desc():
    return "Replace all instances in an auto-scaling group with new instances."

def main(*args):
    """ Recycle all EC2 instances in auto-scaling group
    """
    # Parse command line options
    parser = argparse.ArgumentParser(description='Update launch configuration')
    parser.add_argument('-c', '--config_name', action="store", required=True)

    unknown = []
    args, unknown = parser.parse_known_args()
    if unknown:
        print "Unknown arguments: " + ' '.join(unknown)
        sys.exit(1)

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
    print "Getting old instances Id..."
    sys.stdout.flush()
    (status,output) = commands.getstatusoutput(lb_cmd)
    instance_pat = re.compile('i-\w+')
    if status != 0:
        print "ERROR in getting instances from elb " + elb
        print output
    else:
       old_instances = instance_pat.findall(output)     

    # Scale out to keep service capacity while we recycle instances
    double_capacity = str(int(desired_capacity) * 2)
    set_capacity_cmd = ' '.join(['as-set-desired-capacity',
                                  auto_scaling_group_name,
                                  '--desired-capacity',double_capacity])

    print "Increase capacity to %s" % (double_capacity)
    sys.stdout.flush()
    (status,output) = commands.getstatusoutput(set_capacity_cmd)
    print "%s to %s" % (output,double_capacity)
    if status != 0:
        print "ERROR in doubling capacity for " + auto_scaling_group_name
        print output
        sys.exit(1)

    # Make sure all instances are healthy from the ELB's end
    healthy_pat = 'InService'
    while True:
        (status,output) = commands.getstatusoutput(lb_cmd)
        healthy_instances = instance_pat.findall(output)     
        if len(healthy_instances) == int(double_capacity):
            break
        else:
            time.sleep(5)
            print "Waiting for instances healthy status..."
            sys.stdout.flush()

    # Deregister old instances
    deregister_list = ','.join(old_instances)
    lb_cmd = ' '.join(['aws elb deregister-instances-from-load-balancer',
                       '--load-balancer',elb,
                       '--instances', deregister_list])

    print "Schedule to take old instances out of service pool.."
    sys.stdout.flush()
    (status,output) = commands.getstatusoutput(lb_cmd)

    # Reset capacity in 5 minutes from now
    start_time = time.strftime("%Y-%m-%dT%TZ", time.gmtime(time.time() + 300))
    as_cmd = ' '.join(['as-put-scheduled-update-group-action reset-capacity',
                       '-g', auto_scaling_group_name,
                       '--start-time', start_time,
                       '--desired-capacity', desired_capacity])

    (status,output) = commands.getstatusoutput(as_cmd)
    if status != 0:
        print "ERROR in resetting capacity for " + auto_scaling_group_name
        print output
        sys.exit(1)

    print "%s to %s" % (output,desired_capacity)
    sys.exit(0)
    
# Only execute the code when it's called as a script, not just imported.
if __name__ == '__main__':
    main(*sys.argv[1:])
