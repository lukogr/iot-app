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

import logging
import copy
import random
from scapy.all import Ether, IP, UDP
from ryu.lib.bfdlib import BFD_CONTROL_UDP_PORT

from libnovi.ryu.tools import eth_str_to_int, eth_int_to_str, ipv4_str_to_int, ipv4_int_to_str, increment_val
import libnovi.ryu.common.experimenter.match as exp_match
import libnovi.ryu.common.struct as struct

LOG = logging.getLogger(__name__)


MAC_TYPE = ['eth_src', 'eth_dst']
IPV4_TYPE = ['ipv4_src', 'ipv4_dst']
ALLOWED_RANGES = ['eth_src', 'eth_dst', 'in_port', 'ipv4_src',
                  'ipv4_dst', 'mpls_label']


def flow_mod(dp, flow, send=True):
    """Create Flow Mod message

    :param dp: Datapath
    :param flow: Dictionary describing the flow_mod
    :param send: If True the flow_mod is sent"""
    ofp = dp.ofproto
    cmd = flow.get('command', 'add')
    try:
        if isinstance(cmd, str):
            if cmd.startswith('OFPFC'):
                cmd = eval('ofp.%s' % cmd.upper())
            else:
                cmd = eval('ofp.OFPFC_%s' % cmd.upper())
    except:
        raise Exception("Bad Command %d" % flow.get('command', 'add'))

    cookie = int(flow.get('cookie', 0))
    cookie_mask = int(flow.get('cookie_mask', 0))
    tmp = flow.get('table_id', 0)
    try:
        table_id = int(tmp)
    except:
        try:
            if tmp.startswith('OFPTT'):
                table_id = eval("ofp.%s" % tmp.upper())
            else:
                table_id = eval("ofp.OFPTT_%s" % tmp.upper())
        except:
            raise Exception("Unknown table: (OFPTT_)%s" % tmp.upper())
    idle_timeout = int(flow.get('idle_timeout', 0))
    hard_timeout = int(flow.get('hard_timeout', 0))
    priority = int(flow.get('priority', 10))
    buffer_id = int(flow.get('buffer_id', ofp.OFP_NO_BUFFER))
    out_port = int(flow.get('out_port', ofp.OFPP_ANY))
    out_group = int(flow.get('out_group', ofp.OFPG_ANY))
    flags = int(flow.get('flags', 0))

    # Create ranges - Changed to define them with dictionary
    matches = flow.get('match', {})
    tmp_match = {}  # It includes ranges
    next_val = {}   # Next value to use for each match field
    masks = {}      # Masks to be applied on match_fields with range
    steps = {}      # For each match field, increment val depending on the mask
    for key, val in matches.items():
        if key in ALLOWED_RANGES:
            if isinstance(val, (dict)):
                # Save range boundaries as int
                if key in MAC_TYPE:
                    tmp_match[key] = (eth_str_to_int(val['min']),
                                      eth_str_to_int(val['max']))
                    next_val[key] = eth_str_to_int(val['min'])
                    masks[key] = val.get('mask', None)
                    if 'step' in val:
                        steps[key] = val['step']
                    elif 'mask' in val:
                        steps[key] = (eth_str_to_int(masks[key]) ^ 0xFFFFFFFFFFFF) + 1
                    else:
                        steps[key] = 1
                elif key in IPV4_TYPE:
                    tmp_match[key] = (ipv4_str_to_int(val['min']),
                                      ipv4_str_to_int(val['max']))
                    next_val[key] = ipv4_str_to_int(val['min'])
                    masks[key] = val.get('mask', None)
                    if 'step' in val:
                        steps[key] = val['step']
                    elif 'mask' in val:
                        steps[key] = ~ipv4_str_to_int(masks[key]) + 1
                    else:
                        steps[key] = 1
                else:
                    tmp_match[key] = (val['min'], val['max'])
                    next_val[key] = val['min']
            else:
                tmp_match[key] = val
        else:
            if isinstance(val, (dict)):
                tmp_match[key] = val['min']
            else:
                tmp_match[key] = val
    inst = struct.instruction(flow.get('instructions', []))
    # Change match at each loop
    new_match = copy.deepcopy(tmp_match)  # Ranges will be removed here
    for _ in xrange(int(flow.get('n_flows', 1))):
        for m_field in ALLOWED_RANGES:
            if m_field in new_match and m_field in next_val:
                if m_field in MAC_TYPE:
                    new_match[m_field] = eth_int_to_str(next_val[m_field])
                    if masks[m_field]:
                        new_match[m_field] = (new_match[m_field],
                                              masks[m_field])
                elif m_field in IPV4_TYPE:
                    new_match[m_field] = ipv4_int_to_str(next_val[m_field])
                    if masks[m_field]:
                        new_match[m_field] = (new_match[m_field],
                                              masks[m_field])
                else:
                    new_match[m_field] = next_val[m_field]
                next_val[m_field] = increment_val(next_val[m_field],
                                                  tmp_match[m_field],
                                                  steps[m_field])
#         match = to_match(dp, new_match)
        match = exp_match.NoviMatch(**new_match)

        flow_mod = dp.ofproto_parser.OFPFlowMod(
            dp, cookie, cookie_mask, table_id, cmd, idle_timeout,
            hard_timeout, priority, buffer_id, out_port, out_group,
            flags, match=match, instructions=inst)
        if send:
            dp.send_msg(flow_mod)


def group_mod(dp, group):
    cmd_str = group.get('command', 'add')
    try:
        cmd = eval("dp.ofproto.OFPGC_%s" % cmd_str.upper())
    except Exception, e:
        err_msg = "Unknown group command '%s' (Error: %s)" % (cmd_str, e)
        LOG.debug(err_msg)
        raise Exception(err_msg)
    # Group Type
    try:
        type_ = eval("dp.ofproto.OFPGT_%s" % group.get('type', 'indirect').upper())
    except Exception, e:
        err_msg = "Unknown group type (OFPGT_)%s" % (group.get('type', 'indirect').upper())
        LOG.debug(err_msg)
        raise Exception(err_msg)
    # Group ID
    tmp = group.get('group_id')
    if tmp is None:
        LOG.error('A group_id is required when defining a group_mod')
    try:
        group_id = int(tmp)
    except:
        try:
            group_id = eval('dp.ofproto.OFPG_%s' % (tmp.upper()))
        except:
            raise Exception("Unknown group_id: (OFPG_)%s" % tmp.upper())
    # Buckets
    buckets = []
    for bucket in group.get('buckets', []):
        weight = int(bucket.get('weight', 0))
        watch_port = int(bucket.get('watch_port', dp.ofproto.OFPP_ANY))
        watch_group = int(bucket.get('watch_group', dp.ofproto.OFPG_ANY))
        actions = []
        for dic in bucket.get('actions', []):
            act = struct.action(dic)
            if act is not None:
                actions.append(act)
        buckets.append(dp.ofproto_parser.OFPBucket(
            weight, watch_port, watch_group, actions))

    group_mod = dp.ofproto_parser.OFPGroupMod(
        dp, cmd, type_, group_id, buckets)

    return group_mod


def packet_out(dp, pout):
    in_port = pout.get('in_port', dp.ofproto.OFPP_CONTROLLER)
    buffer_id = pout.get('buffer_id', dp.ofproto.OFP_NO_BUFFER)
    action_list = pout.get('actions', [])
    data = pout.get('data', '')

    actions = []
    # If there is a set_bfd action, build the required data
    bfd_present = False
    print action_list
    for act_dict in action_list:
        act = struct.action(act_dict)
        if act is not None:
            actions.append(act)
        if act_dict.get('exp_type', '') == 'set_bfd':
            bfd_present = True

    if bfd_present:
        assert isinstance(data, dict) is True
        assert 'eth_src' in data
        assert 'eth_dst' in data
        assert 'ipv4_src' in data
        assert 'ipv4_dst' in data
        pkt = Ether(src=data['eth_src'], dst=data['eth_dst']) / \
            IP(src=data['ipv4_src'], dst=data['ipv4_dst'], ttl=255) / \
            UDP(sport=random.randint(49152, 65535), dport=BFD_CONTROL_UDP_PORT)
        data = str(pkt)
    pout_built = dp.ofproto_parser.OFPPacketOut(
        dp, buffer_id, in_port, actions, data)

    return pout_built


def table_features(datapath, n_tables, table_id, match_list):
    """Create a Table Features message to change table configuration (Match only)

    :param datapath: Datapath instance, to get the parser for the message
    :param int n_tables: Number of tables in the target switch
    :param int table_id: Number of the table to be modified, or OFPP_ALL to
        change all existing ones. It can also be a list of int
    :param list match_list: List including all match fields which should be
        supported by the table

    :returns OF message: Table Feature message
    """
    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto
    # Prepare Table Features message
    tab_feat = parser.OFPTableFeaturesStatsRequest(datapath, 0)
    tab_feat.body = []

    # List of tables to set
    if isinstance(table_id, (list, tuple)):
        tables = table_id
    elif table_id == ofproto.OFPP_ALL:
        tables = range(0, n_tables)
    else:
        tables = [table_id]

    # All actions and all instructions are always supported (except GOTO in last table)
    all_actions = [parser.OFPActionId(ofproto.OFPAT_OUTPUT),
                   parser.OFPActionId(ofproto.OFPAT_COPY_TTL_OUT),
                   parser.OFPActionId(ofproto.OFPAT_COPY_TTL_IN),
                   parser.OFPActionId(ofproto.OFPAT_SET_MPLS_TTL),
                   parser.OFPActionId(ofproto.OFPAT_DEC_MPLS_TTL),
                   parser.OFPActionId(ofproto.OFPAT_PUSH_VLAN),
                   parser.OFPActionId(ofproto.OFPAT_POP_VLAN),
                   parser.OFPActionId(ofproto.OFPAT_PUSH_MPLS),
                   parser.OFPActionId(ofproto.OFPAT_POP_MPLS),
                   parser.OFPActionId(ofproto.OFPAT_GROUP),
                   parser.OFPActionId(ofproto.OFPAT_SET_NW_TTL),
                   parser.OFPActionId(ofproto.OFPAT_DEC_NW_TTL),
                   parser.OFPActionId(ofproto.OFPAT_SET_FIELD),
                   parser.OFPActionId(ofproto.OFPAT_PUSH_PBB),
                   parser.OFPActionId(ofproto.OFPAT_POP_PBB)]
    all_instructions = [parser.OFPInstructionId(ofproto.OFPIT_GOTO_TABLE),
                        parser.OFPInstructionId(ofproto.OFPIT_WRITE_METADATA),
                        parser.OFPInstructionId(ofproto.OFPIT_WRITE_ACTIONS),
                        parser.OFPInstructionId(ofproto.OFPIT_APPLY_ACTIONS),
                        parser.OFPInstructionId(ofproto.OFPIT_CLEAR_ACTIONS),
                        parser.OFPInstructionId(ofproto.OFPIT_METER)]
    OxmId = exp_match.NoviOxmId
    all_set_field = [OxmId(3),OxmId(4),OxmId(5),OxmId(6),OxmId(7),OxmId(8),OxmId(9),
                     OxmId(10),OxmId(11),OxmId(12),OxmId(13),OxmId(14),OxmId(15),
                     OxmId(16),OxmId(17),OxmId(18),OxmId(19),OxmId(20),OxmId(21),
                     OxmId(22),OxmId(23),OxmId(24),OxmId(25),OxmId(26),OxmId(27),
                     OxmId(28),OxmId(29),OxmId(30),OxmId(31),OxmId(32),OxmId(33),
                     OxmId(34),OxmId(35),OxmId(36),OxmId(37)]

    for tab in tables:
        tf_stats = parser.OFPTableFeaturesStats(table_id=tab, name='table_%d' % tab,
                                                metadata_match=0, metadata_write=0,
                                                config=0, max_entries=0, properties=[])
        # Instructions
        p_inst = parser.OFPTableFeaturePropInstructions(ofproto.OFPTFPT_INSTRUCTIONS)
        if tab == n_tables-1:
            all_instructions = filter(lambda x: x.type != ofproto.OFPIT_GOTO_TABLE, all_instructions)
        p_inst.instruction_ids = all_instructions
        # Next Tables
        p_next = parser.OFPTableFeaturePropNextTables(ofproto.OFPTFPT_NEXT_TABLES)
        nt = []
        for n in range(tab+1, n_tables):
            nt.append(n)
        p_next.table_ids = nt
        # Write Actions
        p_wa = parser.OFPTableFeaturePropActions(ofproto.OFPTFPT_WRITE_ACTIONS)
        p_wa.action_ids = all_actions
        # Apply Actions
        p_aa = parser.OFPTableFeaturePropActions(ofproto.OFPTFPT_APPLY_ACTIONS)
        p_aa.action_ids = all_actions
        # Match Property
        p_match = parser.OFPTableFeaturePropOxm(ofproto.OFPTFPT_MATCH)
        oxm = []
        for match in match_list:
            if match in struct.oxm_types:
                class_, type_ = struct.oxm_types[match]
                oxm.append(OxmId(type_, class_=class_))
        p_match.oxm_ids = oxm
        # Wildcards Property
        p_wild = parser.OFPTableFeaturePropOxm(ofproto.OFPTFPT_WILDCARDS)
        p_wild.oxm_ids = oxm
        # Write Setfield
        p_ws = parser.OFPTableFeaturePropOxm(ofproto.OFPTFPT_WRITE_SETFIELD)
        p_ws.oxm_ids = all_set_field
        # Apply Setfield
        p_as = parser.OFPTableFeaturePropOxm(ofproto.OFPTFPT_APPLY_SETFIELD)
        p_as.oxm_ids = all_set_field
        # Add properties to table features stats list
        tf_stats.properties = [p_inst, p_next, p_wa, p_aa, p_match, p_wild, p_ws, p_as]
        tab_feat.body.append(tf_stats)
    return tab_feat
