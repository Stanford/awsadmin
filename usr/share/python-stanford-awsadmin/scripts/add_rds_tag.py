#!/usr/bin/env python
#
# Copyright 2013
#         The Board of Trustees of the Leland Stanford Junior University

"""Add tags to rds database

This script creates a new db instance in AWS.

Options:
         -i / --db-identifier=<value>
         -c / --comment=<value>
         -p / --psa-core=<value>
             format example: "IDG-WEB"
         -h / --help
            Print this message and exit
                
"""

__author__ = 'sfeng@stanford.edu'

import sys
import getopt
import time
import string
import random
import re
import commands

import paths
import awsadmin_cfg
from lib.Utils import add_rds_tag

def short_desc():
    return "Add a tag to a RDS instance."

def main(*args):
    """ Add a tag to a RDS instance
    """
    # Parse command line options
    try:
        opts, args = getopt.getopt(args, 'hi:c:p:', ['help', 
        'db-identifier=', 'comment=', 'psa-core='])
    except getopt.error, msg:
        print msg
        sys.exit(1)

    # Default values
    psa_core = comment = pta = ''

    # Process options
    for option, arg in opts:
        if option in ('-i', '--db-identifier'):
            db_identifier=arg
        elif option in ('-c','--comment'):
            comment = arg
        elif option in ('-p','--psa-core'):
            psa_core = arg
            try:
                pta = awsadmin_cfg.PSA_CORE[psa_core]
            except KeyError:
                print "Wrong psa_core type. Should be one of the following:"
                print ', '.join(awsadmin_cfg.PSA_CORE.keys())
                sys.exit(1)
        elif option in ('-h', '--help'):
            print __doc__
            sys.exit(0)

    if not psa_core:
        print "psa-core is required."
        sys.exit(1)

    resource_name = awsadmin_cfg.RDS_ARN + db_identifier
    print resource_name
    (status,output) = add_rds_tag(resource_name,psa_core,pta)
    if comment:
        (status,output) = add_rds_tag(resource_name,'comment',comment)

    if status != 0:
       print "ERROR in adding tags for " + db_identifier
       print output
    else:
       print output
       sys.exit(0)
    
# Only execute the code when it's called as a script, not just imported.
if __name__ == '__main__':
    main(*sys.argv[1:])
