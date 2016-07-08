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

"""Constructors for common structures"""
import logging
import yaml
from ryu.ofproto import ether
import ryu.ofproto.ofproto_v1_3 as ofp_v13
import ryu.ofproto.ofproto_v1_4 as ofp_v14
from ryu.lib.ofctl_v1_3 import str_to_int
from libnovi.ryu.common.experimenter.const import NOVI_MATCH_UDP_PAYLOAD, NOVI_MATCH_IP_PAYLOAD

LOG = logging.getLogger(__name__)


with open('config.yaml') as conffile:
    config = yaml.load(conffile)
    if config['ofp_version'] == ofp_v13.OFP_VERSION:
        import libnovi.ryu.of13.experimenter.action as exp_act
        import ryu.ofproto.ofproto_v1_3_parser as parser
        ofproto = ofp_v13
    elif config['ofp_version'] == ofp_v14.OFP_VERSION:
        import libnovi.ryu.of14.experimenter.action as exp_act
        import ryu.ofproto.ofproto_v1_4_parser as parser
        ofproto = ofp_v14
    else:
        print "OF Version %s not supported, using 1.3 Ryu parser. Please Fix config.yaml" % config['ofp_version']
        import ryu.ofproto.ofproto_v1_3_parser as parser
        ofproto = ofp_v13


def instruction(d_inst):
    """Build Instruction from dictionary"""
    inst = []
    for i in d_inst:
        inst_type = i.get('type').upper()
        if inst_type in ['GOTO_TABLE', 'GOTO']:
            table_id = int(i.get('table_id'))
            inst.append(parser.OFPInstructionGotoTable(table_id))
        elif inst_type == 'WRITE_METADATA':
            metadata = str_to_int(i.get('metadata'))
            metadata_mask = (str_to_int(i['metadata_mask'])
                             if 'metadata_mask' in i
                             else parser.UINT64_MAX)
            inst.append(parser.OFPInstructionWriteMetadata(metadata, metadata_mask))
        elif inst_type in ('WRITE_ACTIONS', 'WRITE'):
            actions = []
            acts = i.get('actions')
            for a in acts:
                act = action(a)
                if action is not None:
                    actions.append(act)
            inst.append(parser.OFPInstructionActions(ofproto.OFPIT_WRITE_ACTIONS, actions))
        elif inst_type in ('APPLY_ACTIONS', 'APPLY'):
            actions = []
            acts = i.get('actions')
            for a in acts:
                act = action(a)
                if action is not None:
                    actions.append(act)
            inst.append(parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions))
        elif inst_type in ('CLEAR_ACTIONS', 'CLEAR'):
            inst.append(parser.OFPInstructionActions(ofproto.OFPIT_CLEAR_ACTIONS, []))
        elif inst_type == 'METER':
            meter_id = int(i.get('meter_id'))
            inst.append(parser.OFPInstructionMeter(meter_id))
        else:
            LOG.debug('Unknown action type: %s' % inst_type)

    return inst


def action(act_dict):
    """Build Action from dictionary"""
    try:
        act_type = act_dict.get('type').lower()
        if act_type == 'output':
            port = act_dict.get('port')
            if isinstance(port, str):
                outport = eval('ofproto.OFPP_%s' % port.upper())
            else:
                outport = int(act_dict.get('port'))
            act = parser.OFPActionOutput(port=outport,
                                         max_len=act_dict.get('max_len', ofproto.OFPCML_MAX))
        elif act_type == 'copy_ttl_out':
            act = parser.OFPActionCopyTtlOut()
        elif act_type == 'copy_ttl_in':
            act = parser.OFPActionCopyTtlIn()
        elif act_type == 'set_mpls_ttl':
            act = parser.OFPActionSetMplsTtl(mpls_ttl=act_dict.get('mpls_ttl'))
        elif act_type == 'dec_mpls_ttl':
            act = parser.OFPActionDecMplsTtl()
        elif act_type == 'push_vlan':
            act = parser.OFPActionPushVlan(ethertype=act_dict.get('ethertype', ether.ETH_TYPE_8021Q))
        elif act_type == 'pop_vlan':
            act = parser.OFPActionPopVlan()
        elif act_type == 'push_mpls':
            act = parser.OFPActionPushMpls(ethertype=act_dict.get('ethertype', ether.ETH_TYPE_MPLS))
        elif act_type == 'pop_mpls':
            act = parser.OFPActionPopMpls(ethertype=act_dict.get('ethertype', ether.ETH_TYPE_IP))
        elif act_type == 'set_queue':
            act = parser.OFPActionSetQueue(queue_id=act_dict.get('queue_id'))
        elif act_type == 'group':
            act = parser.OFPActionGroup(group_id=act_dict.get('group_id'))
        elif act_type == 'set_nw_ttl':
            act = parser.OFPActionSetNwTtl(nw_ttl=act_dict.get('nw_ttl'))
        elif act_type == 'dec_nw_ttl':
            act = parser.OFPActionDecNwTtl()
        elif act_type == 'set_field':

            #kwargs = act_dict.get('field')
            #act = parser.OFPActionSetField(**kwargs)
            
            field = act_dict.get('field')
            value = act_dict.get('value')            
            act = parser.OFPActionSetField(**{field: value})


        elif act_type == 'push_pbb':
            act = parser.OFPActionPushVlan(ethertype=act_dict.get('ethertype', ether.ETH_TYPE_8021AD))
        elif act_type == 'pop_pbb':
            act = parser.OFPActionPopMpls()
        elif act_type == 'experimenter':
            # Set IP/UDP payload
            if act_dict.get('exp_type') in ['set_udp_payload', 'set_ip_payload']:
                for required in ['offset', 'value']:
                    assert required in act_dict.keys(), "Size, Offset, and Value must be specified in set_*_payload action"
                _size = act_dict.get('size', len(act_dict.get('value')))
                if act_dict.get('exp_type') == 'set_udp_payload':
                    act = exp_act.SetUdpPayload(_size, act_dict.get('offset'),
                                                act_dict.get('value'),
                                                act_dict.get('mask', []))
                elif act_dict.get('exp_type') == 'set_ip_payload':
                    act = exp_act.SetIpPayload(_size, act_dict.get('offset'),
                                               act_dict.get('value'),
                                               act_dict.get('mask', []))
            # Tunnels
            elif act_dict.get('exp_type') == 'pop_tunnel':
                assert act_dict.get('tunnel_type') is not None, "Tunnel Type must be specified"
                act = exp_act.PopTunnel(act_dict.get('tunnel_type'))
            elif act_dict.get('exp_type') == 'push_tunnel':
                assert act_dict.get('tunnel_type') is not None, "Tunnel Type must be specified"
                act = exp_act.PushTunnel(act_dict.get('tunnel_type'))
            elif act_dict.get('exp_type') == 'push_vxlan':
                act = exp_act.PushVxLAN(
                    act_dict.get('eth_src', '00:00:00:00:00:00'),
                    act_dict.get('eth_dst', '00:00:00:00:00:00'),
                    act_dict.get('ipv4_src', '0.0.0.0'),
                    act_dict.get('ipv4_dst', '0.0.0.0'),
                    act_dict.get('udp_src', 0), act_dict.get('vni', 0))
            elif act_dict.get('exp_type') == 'push_l2gre':
                act = exp_act.PushL2GRE(
                    act_dict.get('eth_src', '00:00:00:00:00:00'),
                    act_dict.get('eth_dst', '00:00:00:00:00:00'),
                    act_dict.get('ipv4_src', '0.0.0.0'),
                    act_dict.get('ipv4_dst', '0.0.0.0'),
                    act_dict.get('key', 0))
            elif act_dict.get('exp_type') == 'push_l2mpls':
                act = exp_act.PushL2MPLS(
                    act_dict.get('eth_src', '00:00:00:00:00:00'),
                    act_dict.get('eth_dst', '00:00:00:00:00:00'),
                    act_dict.get('tunnel_label', 0), act_dict.get('vc_label', 0))
            elif act_dict.get('exp_type') == 'set_bfd':
                assert 'port_no' in act_dict, 'Port Number must be specified in SetBfd action'
                act = exp_act.SetBfd(
                    act_dict.get('port_no'),
                    act_dict.get('my_disc', 1),
                    act_dict.get('interval', 100000),
                    act_dict.get('multiplier', 3))
            else:
                raise Exception("Unkown exp_type: %s" % act_dict.get('exp_type'))

        else:
            raise Exception("Unkown Action type: %s" % act_type)

    except (Exception, AssertionError), e:
        # _, _, tb = sys.exc_info()
        # traceback.print_tb(tb)
        # tb_info = traceback.extract_tb(tb)
        # filename, line, func, text = tb_info[-1]
        LOG.error("Could not create action '%s' with parameters '%s' (error: %s)" %
                  (act_type, act_dict, e))
    return act


# Dictionary to get Match OXM using its name
oxm_types = {'in_port': (ofproto.OFPXMC_OPENFLOW_BASIC, ofproto.OFPXMT_OFB_IN_PORT),  # name: (class, type)
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
            'udp_payload': (ofproto.OFPXMC_EXPERIMENTER, NOVI_MATCH_UDP_PAYLOAD),
            'ip_payload': (ofproto.OFPXMC_EXPERIMENTER, NOVI_MATCH_IP_PAYLOAD)
            }
