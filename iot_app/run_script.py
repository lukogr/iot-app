# Copyright (C) 2016 NoviFlow Inc.
#
# This software was developed at NoviFlow Inc (www.noviflow.com).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License

"""Execute the Python script in the desired path to send RESTful requests.
Multiple scripts can be specified at once and executed in order.
Arguments can also be passed to these scripts.

Usage Example:
    python run_script.py --args arg1=X arg2=Y relative/path/to/script.py another/script.py

To know which arguments a script can use:
    python run_script.py --documentation path/to/script.py
"""

import sys
import argparse
import requests
import yaml
import traceback
from importlib import import_module
import libnovi.ryu.uri as uri

CONFIG_FILE = 'config.yaml'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('filenames', metavar='NAME', type=str, nargs='+',
                        help="List of path/filename.py to execute")
    parser.add_argument('--args', type=str, nargs='+',
                        help="Additional arguments for the scripts")
    parser.add_argument('--description', action="store_true",
                        help="Print information about the specified scripts")

    # Build list of scripts to run
    args = parser.parse_args()
    script_list = []
    for name in args.filenames:
        script_list.append(name.replace('.py', '').replace('/', '.'))

    args_dict = {}
    # Transform the string of arguments in dictionary
    if args.args is not None:
        for argument in args.args:
            for arg_tuple in argument.split(','):
                split_tuple = arg_tuple.split('=')
                if len(split_tuple) == 2:
                    args_dict[split_tuple[0]] = split_tuple[1]
                else:
                    print "Problem parsing argument %s. Format must be <key>=<val>." % arg_tuple

    ryu_uri = 'http://127.0.0.1:8080'
    with open(CONFIG_FILE) as yaml_file:
        yaml_loaded = yaml.load(yaml_file)
        ryu_uri = 'http://%s:%d' % (yaml_loaded['ryu_ip_address'],
                                    yaml_loaded['ryu_rest_tcp_port'])
    print "-------------------- NoviRest Ryu --------------------"
    print " - ryu-manager URI: %s" % ryu_uri

    # Verify that NoviRest is running
    rest_present = requests.get(ryu_uri + uri.CHECK_NOVIREST_MODULE).status_code
    if rest_present != requests.codes.ok:
        print "NoviRest is not responding. Exiting."
        sys.exit()

    # Determine DPID
    dpid_list = requests.get(ryu_uri + uri.DPID_LIST).json().keys()
    if len(dpid_list) == 0:
        print " - No switch connected to Ryu. Exiting."
        sys.exit(0)
    elif len(dpid_list) == 1:
        dpid = int(dpid_list[0])
        print " - Connected to DPID: %d (0x%x)" % (dpid, dpid)
    else:
        print "Found multiple switches connected:"
        for idx in range(len(dpid_list)):
            sw_dpid = int(dpid_list[idx])
            print "   [%d] %d (0x%x)" % (idx+1, sw_dpid, sw_dpid)
        sel_dpid = raw_input("Select the DPID of the switch which should be used [1-%d]: "
                             % len(dpid_list))
        try:
            dpid = int(dpid_list[int(sel_dpid)-1])
        except:
            print "Wrong selection (%s). Exiting" % sel_dpid
            sys.exit()

    print "\n-------------------- Start Execution --------------------\n"
    # Execute one script at the time
    for script in script_list:
        print " - Script: %s" % script
        try:
            exe_script = import_module(script)
            if args.description:
                print "%s\n" % exe_script.__doc__
            else:
                exe_script.run(dpid, ryu_uri, args=args_dict)
        except Exception, e:
            print "Cannot import/execute script %s (Error: %s)" % (script, e)
            print "-- Traceback ----"
            traceback.print_exc(file=sys.stdout)
