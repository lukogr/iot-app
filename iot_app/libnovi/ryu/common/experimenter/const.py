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

import ryu.ofproto.ofproto_v1_4 as ofproto

# Experimenter
NOVIFLOW_EXPERIMENTER_ID = 0xff000002

CUSTOMER_NOVIFLOW = 0xff
RESERVED = 0x00

EXP_MSG_UDP_PAYLOAD = 0x00 # Experimenter subtype for setting UDP payload size and offset
EXP_MSG_IP_PAYLOAD = 0x01 # Experimenter subtype for setting IP payload size and offset


########################################################################
# Match
########################################################################
NOVI_MATCH_UDP_PAYLOAD = 1
NOVI_MATCH_IP_PAYLOAD = 2

# MATCH_CLS_UDP_PAYLOAD = ofproto.OFPXMC_EXPERIMENTER<<16 | NOVI_MATCH_UDP_PAYLOAD<<9 | False<<8
# MATCH_CLS_UDP_PAYLOAD_W = ofproto.OFPXMC_EXPERIMENTER<<16 | NOVI_MATCH_UDP_PAYLOAD<<9 | True<<8


########################################################################
# Actions
########################################################################
NOVI_ACTION_SET_UDP_PAYLOAD = 0
NOVI_ACTION_SET_IP_PAYLOAD = 1
NOVI_ACTION_PUSH_TUNNEL = 2
NOVI_ACTION_POP_TUNNEL = 3
NOVI_ACTION_SET_BFD = 4

# Tunnels
TUNNEL_TYPE_VXLAN = 0
TUNNEL_TYPE_L2GRE = 1
TUNNEL_TYPE_L2MPLS = 2

PUSH_TUNNEL_NO_PARAM = 0
PUSH_TUNNEL_WITH_PARAM = 1

########################################################################
# Properties
########################################################################
PORT_DESC_BFD_PROP_TYPE = 0
exp_prop_subtype_map = {
    PORT_DESC_BFD_PROP_TYPE: 'PORT_DESC_BFD_PROP_TYPE'
}

BFD_STATUS_DISABLED = 0
BFD_STATUS_DOWN = 1
BFD_STATUS_UP = 2
BFD_STATUS_INCOMPATIBLE = 3
port_desc_bfd_status_map = {
    BFD_STATUS_DISABLED: "BFD_STATUS_DISABLED",
    BFD_STATUS_DOWN: "BFD_STATUS_DOWN",
    BFD_STATUS_UP: "BFD_STATUS_UP",
    BFD_STATUS_INCOMPATIBLE: "BFD_STATUS_INCOMPATIBLE",
}


# Dictionary to relate the match name to its int value
oxm_types = {'in_port': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IN_PORT), # name: (class, type)
            'in_phy_port': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IN_PHY_PORT),
            'metadata': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_METADATA),
            'eth_dst': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ETH_DST),
            'eth_src': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ETH_SRC),
            'eth_type': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ETH_TYPE),
            'vlan_vid': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_VLAN_VID),
            'vlan_pcp': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_VLAN_PCP),
            'ip_dscp': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IP_DSCP),
            'ip_ecn': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IP_ECN),
            'ip_proto': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IP_PROTO),
            'ipv4_src': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IPV4_SRC),
            'ipv4_dst': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IPV4_DST),
            'tcp_src': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_TCP_SRC),
            'tcp_dst': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_TCP_DST),
            'udp_src': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_UDP_SRC),
            'udp_dst': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_UDP_DST),
            'sctp_src': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_SCTP_SRC),
            'sctp_dst': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_SCTP_DST),
            'icmpv4_type': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ICMPV4_TYPE),
            'icmpv4_code': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ICMPV4_CODE),
            'arp_op': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ARP_OP),
            'arp_spa': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ARP_SPA),
            'arp_tpa': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ARP_TPA),
            'arp_sha': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ARP_SHA),
            'arp_tha': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ARP_THA),
            'ipv6_src': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IPV6_SRC),
            'ipv6_dst': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IPV6_DST),
            'ipv6_flabel': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IPV6_FLABEL),
            'icmpv6_type': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ICMPV6_TYPE),
            'icmpv6_code': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_ICMPV6_CODE),
            'ipv6_nd_target': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IPV6_ND_TARGET),
            'ipv6_nd_sll': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IPV6_ND_SLL),
            'ipv6_nd_tll': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IPV6_ND_TLL),
            'mpls_label': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_MPLS_LABEL),
            'mpls_tc': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_MPLS_TC),
            'mpls_bos': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_MPLS_BOS),
            'pbb_isid': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_PBB_ISID),
            'tunnel_id': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_TUNNEL_ID),
            'ipv6_exthdr': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IPV6_EXTHDR),
            'exp_udp_payload': (ofproto.OFPXMC_EXPERIMENTER, NOVI_MATCH_UDP_PAYLOAD),
            'exp_ip_payload': (ofproto.OFPXMC_EXPERIMENTER, NOVI_MATCH_IP_PAYLOAD)
            }
