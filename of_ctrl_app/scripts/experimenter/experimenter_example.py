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

import requests
import json
import libnovi.ryu.uri as uri


def run(dpid, ryu_uri, args={}):
    idx = 0

    ##################
    # IP/UDP PAYLOAD #
    ##################

    # Before sending flow_mod matching on UDP/IP payload the table
    # must be configured to support these match field and specify their
    # size and offset
    # The following CLIs can be used:
    #
    # set config table tableid 0 matchfields 0 expmatchfields 1 2
    # set config table tableid 0 udppayloadmatch size 3 offset 12
    # set config table tableid 0 ippayloadmatch size 7 offset 20
    #
    # Otherwise, table_features can be used to configure the match fields
    # and experimenter messages can configure size and offset of UDP/IP
    # payload match, as shown below

    # Configure match fields in table 0
    print "Configure match fields in table 0 ti support IP and UDP payload"
    tf = {'dpid': dpid, 'table_id': 0,
          'match_fields': ['in_port', 'udp_payload', 'ip_payload']}
    requests.post(ryu_uri+(uri.SET_TABLE_FEATURES), data=json.dumps(tf)).text

    # Configure UDP payload match size and offset
    print "Configure UDP payload match size and offset"
    udp_config = {'dpid': dpid, 'table_id': 0, 'size': 3, 'offset': 12}
    requests.post(ryu_uri+(uri.UDP_PAYLOAD_CONFIG), data=json.dumps(udp_config)).text

    # Configure IP payload match size and offset
    print "Configure IP payload match size and offset"
    ip_config = {'dpid': dpid, 'table_id': 0, 'size': 7, 'offset': 20}
    requests.post(ryu_uri+(uri.IP_PAYLOAD_CONFIG), data=json.dumps(ip_config)).text

    print "Add flow_mods to use match and set UDP and IP payload"
    # Flow Mod matching on UDP payload (size=3)
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'udp_payload': [0x77, 0x88, 0x99]},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    # Flow Mod matching on IP payload (size=7)
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'ip_payload': "abcdefg"},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    # Flow Mod using the set UDP payload action
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'in_port': idx},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'experimenter',
                                         'exp_type': 'set_udp_payload',
                                         'offset': 5, 'value': "AAA"},
                                        {'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    # Flow Mod using the set IP payload action
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'in_port': idx},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'experimenter',
                                         'exp_type': 'set_ip_payload',
                                         'offset': 7, 'value': [0xff, 0x12, 5, 0xab]},
                                        {'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    # Flow Mod using the set IP payload action with mask
    # Value for bits with mask==0 will be forced to 0 by Ryu
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'in_port': idx},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'experimenter',
                                         'exp_type': 'set_ip_payload',
                                         'offset': 7,
                                         'value': [0xff, 0x12, 5, 'b'],  # Because of the mask this will become = 0x330005a0
                                         'mask': [0x33, 0x00, 0xff, 0xf0]},
                                        {'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    ###########
    # TUNNELS #
    ###########

    print "Add flow_mods to use the push/pop tunnel actions (L2MPLS, L2GRE, and VxLAN)"
    # Flow Mod using the Push L2MPLS action with parameters
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'in_port': 1},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'experimenter',
                                         'exp_type': 'push_l2mpls',
                                         'eth_src': "11:11:11:11:11:11",
                                         'eth_dst': [1, 2, 4, 5, 6, 7],
                                         'tunnel_label': 100,
                                         'vc_label': 200},
                                        {'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    # Flow Mod using the Push L2GRE action with parameters
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'in_port': idx},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'experimenter',
                                         'exp_type': 'push_l2gre',
                                         'eth_src': "22:33:22:33:22:33",
                                         'eth_dst': [1, 2, 4, 5, 6, 7],
                                         'ipv4_src': '1.1.1.1', 'ipv4_dst': 0x01020304,
                                         'key': 99},
                                        {'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    # Flow Mod using the Push VxLAN action with parameters
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'in_port': idx},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'experimenter',
                                         'exp_type': 'push_vxlan',
                                         'eth_src': "10:20:a0:b0:c0:d0",
                                         'eth_dst': [1, 2, 4, 5, 6, 7],
                                         'ipv4_src': '1.1.1.1', 'ipv4_dst': 0x01020304,
                                         'udp_src': 123, 'vni': 77},
                                        {'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    # Flow Mod using the Push Tunnel action without parameters
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'in_port': idx},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'experimenter',
                                         'exp_type': 'push_tunnel', 'tunnel_type': 'vxlan'},  # tunnel_type can be any of the previous ones
                                        {'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    # Flow Mod using the Pop Tunnel
    fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': idx,
          'cookie': idx, 'match': {'in_port': idx},
          'instructions': [{'type': 'apply',
                            'actions': [{'type': 'experimenter',
                                         'exp_type': 'pop_tunnel', 'tunnel_type': 'vxlan'},  # tunnel_type can be any of the previous ones
                                        {'type': 'output', 'port': 1}]}]}
    requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
    idx += 1

    #########
    # Group #
    #########
    print "Add a group to use the push_tunnel action"
    gm = {'dpid': dpid, 'command': 'add', 'type': 'indirect', 'group_id': 5,
          'buckets': [{'weight': 1, 'actions': [{'type': 'experimenter',
                                                 'exp_type': 'push_tunnel', 'tunnel_type': 'l2mpls'}]}]}
    requests.post(ryu_uri+(uri.GROUP_MOD), data=json.dumps(gm)).text


if __name__ == '__main__':
    ryu_addr = '127.0.0.1'
    dpid = int(requests.get(ryu_addr + uri.DPID_LIST).json().keys()[0])
    run(dpid, ryu_addr)
