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

import struct
import yaml
import ryu.ofproto.ofproto_v1_3 as ofp_v13
import ryu.ofproto.ofproto_v1_4 as ofp_v14
import libnovi.ryu.common.experimenter.const as exp_const
from libnovi.ryu.tools import eth_str_to_list, ipv4_str_to_int

with open('config.yaml') as conffile:
    config = yaml.load(conffile)
    if config['ofp_version'] == ofp_v13.OFP_VERSION:
        import ryu.ofproto.ofproto_v1_3_parser as parser
        ofproto = ofp_v13
    elif config['ofp_version'] == ofp_v14.OFP_VERSION:
        import ryu.ofproto.ofproto_v1_4_parser as parser
        ofproto = ofp_v14
    else:
        print "OF Version %s not supported, using 1.3 Ryu parser. Please Fix config.yaml" % config['ofp_version']
        import ryu.ofproto.ofproto_v1_3_parser as parser
        ofproto = ofp_v13


# Set UDP/IP Payload


class BasicSetPayload(parser.OFPActionExperimenter):
    """Basic generic class for Set Payload actions"""
    def __init__(self, subtype, size, offset, data, mask=[]):
        self.act_exp_type = subtype
        self.size = size
        self.offset = offset
        self.data = data
        self.mask = mask
        if len(mask) > 0:
            assert len(mask) == len(data), "Data and and Mask must have the same length"
            self.hasmask = True
            for idx in range(len(mask)):
                if isinstance(data[idx], str):
                    d = ord(data[idx])
                else:
                    d = data[idx]
                if isinstance(mask[idx], str):
                    m = ord(mask[idx])
                else:
                    m = mask[idx]
                self.data[idx] = d & m
        else:
            self.hasmask = False
        exp_type = exp_const.CUSTOMER_NOVIFLOW << 24 | exp_const.RESERVED << 16 | self.act_exp_type
        # uint8 size, uint16 offset, uint8 hasmask, [] data, <[] mask>
        fmt = "!IBHB"
        body = struct.pack(fmt, exp_type, size, offset, self.hasmask)
        for byte_el in data:
            if isinstance(byte_el, str):
                body += struct.pack('!B', ord(byte_el))
            else:
                body += struct.pack('!B', byte_el)
        for byte_el in self.mask:
            if isinstance(byte_el, str):
                body += struct.pack('!B', ord(byte_el))
            else:
                body += struct.pack('!B', byte_el)

        parser.OFPActionExperimenter.__init__(self, exp_const.NOVIFLOW_EXPERIMENTER_ID,
                                              data=body)

    def get_action_type(self):
        """Return the experimenter action subtype"""
        return self.act_exp_type

    def show(self):
        """Return a description of the action"""
        desc = "Experimenter Action"
        desc += "\tAction Exp Type: %d" % self.act_exp_type
        desc += "\tSize: %d" % self.size
        desc += "\tOffset: %d" % self.offset
        desc += "\tHasMask: %s" % self.hasmask
        desc += "\tData: %s" % self.data
        desc += "\tMask: %s" % self.mask
        return desc


class SetUdpPayload(BasicSetPayload):
    """Action Set UDP Payload"""
    def __init__(self, size, offset, data, mask=[]):
        BasicSetPayload.__init__(self, exp_const.NOVI_ACTION_SET_UDP_PAYLOAD,
                                 size, offset, data, mask)


class SetIpPayload(BasicSetPayload):
    """Action Set IP Payload"""
    def __init__(self, size, offset, data, mask=[]):
        BasicSetPayload.__init__(self, exp_const.NOVI_ACTION_SET_IP_PAYLOAD,
                                 size, offset, data, mask)

# Tunnels


class PushTunnel(parser.OFPActionExperimenter):
    """Push Tunnel without parameters

    uint32 exp_type
    uint8 tunnel_type
    uint8 flags (with or without parameters) = 0
    uint8 pad[2]
    """
    def __init__(self, tunnel_type, flags=exp_const.PUSH_TUNNEL_NO_PARAM, data=None):
        self.exp_type = exp_const.CUSTOMER_NOVIFLOW << 24 | exp_const.RESERVED << 16 | exp_const.NOVI_ACTION_PUSH_TUNNEL
        if isinstance(tunnel_type, str):
            self.tunnel_type = eval('exp_const.TUNNEL_TYPE_%s' % tunnel_type.upper())
        else:
            self.tunnel_type = tunnel_type
        self.flags = flags
        pad = [0, 0]
        fmt = "!LBB"
        body = struct.pack(fmt, self.exp_type, self.tunnel_type, self.flags)

        if data is not None:
            body += data
        else:
            fmt = "!BB"
            body += struct.pack(fmt, pad[0], pad[1])

        super(PushTunnel, self).__init__(exp_const.NOVIFLOW_EXPERIMENTER_ID,
                                         data=body)

    def get_action_type(self):
        """Return the experimenter action subtype"""
        return self.exp_type

    def show(self):
        """Return a description of the action"""
        desc = "Experimenter Action: Push Tunnel\n"
        desc += "\tAction Exp Type: %d (0x%x)\n" % (self.exp_type, self.exp_type)
        desc += "\tTunnel Type: %d\n" % self.tunnel_type
        desc += "\tFlags: %d\n" % self.flags
        return desc


class PushVxLAN(PushTunnel):
    """Push VxLAN Tunnel with parameters

    uint32 exp_type
    uint8 tunnel_type = 0
    uint8 flags (with or without parameters) = 1
    uint_8 eth_src[6]
    uint_8 eth_dst[6]
    uint_32 ipv4_src
    uint_32 ipv4_dst
    uint_16 udp_src
    unit_32 vni
    """
    def __init__(self, eth_src, eth_dst, ipv4_src, ipv4_dst, udp_src, vni):
        self.exp_type = exp_const.CUSTOMER_NOVIFLOW << 24 | exp_const.RESERVED << 16 | exp_const.NOVI_ACTION_PUSH_TUNNEL
        self.tunnel_type = exp_const.TUNNEL_TYPE_VXLAN
        self.flags = exp_const.PUSH_TUNNEL_WITH_PARAM
        if isinstance(eth_src, str):
            self.eth_src = eth_str_to_list(eth_src)
        else:
            self.eth_src = eth_src
        if isinstance(eth_dst, str):
            self.eth_dst = eth_str_to_list(eth_dst)
        else:
            self.eth_dst = eth_dst
        if isinstance(ipv4_src, str):
            self.ipv4_src = ipv4_str_to_int(ipv4_src)
        else:
            self.ipv4_src = ipv4_src
        if isinstance(ipv4_dst, str):
            self.ipv4_dst = ipv4_str_to_int(ipv4_dst)
        else:
            self.ipv4_dst = ipv4_dst
        self.udp_src = udp_src
        self.vni = vni

        body = ''
        for b in self.eth_src:
            body += struct.pack("!B", b)
        for b in self.eth_dst:
            body += struct.pack("!B", b)
        fmt = "!LLHL"
        body += struct.pack(fmt, self.ipv4_src, self.ipv4_dst, self.udp_src, self.vni)

        super(PushVxLAN, self).__init__(tunnel_type=self.tunnel_type,
                                        flags=self.flags, data=body)

    def show(self):
        """Return a description of the action"""
        desc = super(PushVxLAN, self).show()
        desc += "\tEth Src: %s\n" % self.eth_src
        desc += "\tEth Dst: %s\n" % self.eth_dst
        desc += "\tIPv4 Src: %s\n" % self.ipv4_src
        desc += "\tIPv4 Dst: %s\n" % self.ipv4_dst
        desc += "\tUDP Src: %s\n" % self.udp_src
        desc += "\tVNI: %s\n" % self.vni
        return desc


class PushL2GRE(PushTunnel):
    """Push L2GRE Tunnel with parameters

    uint32 exp_type
    uint8 tunnel_type = 0
    uint8 flags (with or without parameters) = 1
    uint_8 eth_src[6]
    uint_8 eth_dst[6]
    uint_32 ipv4_src
    uint_32 ipv4_dst
    unit_32 key
    uint_8 pad[2]
    """
    def __init__(self, eth_src, eth_dst, ipv4_src, ipv4_dst, key):
        self.exp_type = exp_const.CUSTOMER_NOVIFLOW << 24 | exp_const.RESERVED << 16 | exp_const.NOVI_ACTION_PUSH_TUNNEL
        self.tunnel_type = exp_const.TUNNEL_TYPE_L2GRE
        self.flags = exp_const.PUSH_TUNNEL_WITH_PARAM
        if isinstance(eth_src, str):
            self.eth_src = eth_str_to_list(eth_src)
        else:
            self.eth_src = eth_src
        if isinstance(eth_dst, str):
            self.eth_dst = eth_str_to_list(eth_dst)
        else:
            self.eth_dst = eth_dst
        if isinstance(ipv4_src, str):
            self.ipv4_src = ipv4_str_to_int(ipv4_src)
        else:
            self.ipv4_src = ipv4_src
        if isinstance(ipv4_dst, str):
            self.ipv4_dst = ipv4_str_to_int(ipv4_dst)
        else:
            self.ipv4_dst = ipv4_dst
        self.key = key
        pad = [0, 0]

        body = ''
        for b in self.eth_src:
            body += struct.pack("!B", b)
        for b in self.eth_dst:
            body += struct.pack("!B", b)
        fmt = "!LLL"
        body += struct.pack(fmt, self.ipv4_src, self.ipv4_dst, self.key)
        fmt = "!BB"
        body += struct.pack(fmt, pad[0], pad[1])

        super(PushL2GRE, self).__init__(tunnel_type=self.tunnel_type,
                                        flags=self.flags, data=body)

    def show(self):
        """Return a description of the action"""
        desc = super(PushL2GRE, self).show()
        desc += "\tEth Src: %s\n" % self.eth_src
        desc += "\tEth Dst: %s\n" % self.eth_dst
        desc += "\tIPv4 Src: %s\n" % self.ipv4_src
        desc += "\tIPv4 Dst: %s\n" % self.ipv4_dst
        desc += "\tKey: %s\n" % self.key
        return desc


class PushL2MPLS(PushTunnel):
    """Push L2GRE Tunnel with parameters

    uint32 exp_type
    uint8 tunnel_type = 0
    uint8 flags (with or without parameters) = 1
    uint_8 eth_src[6]
    uint_8 eth_dst[6]
    uint_32 tunnel_label
    uint_32 vc_label
    uint_8 pad[6]
    """
    def __init__(self, eth_src, eth_dst, tunnel_label, vc_label):
        self.exp_type = exp_const.CUSTOMER_NOVIFLOW << 24 | exp_const.RESERVED << 16 | exp_const.NOVI_ACTION_PUSH_TUNNEL
        self.tunnel_type = exp_const.TUNNEL_TYPE_L2MPLS
        self.flags = exp_const.PUSH_TUNNEL_WITH_PARAM
        if isinstance(eth_src, str):
            self.eth_src = eth_str_to_list(eth_src)
        else:
            self.eth_src = eth_src
        if isinstance(eth_dst, str):
            self.eth_dst = eth_str_to_list(eth_dst)
        else:
            self.eth_dst = eth_dst
        self.tunnel_label = tunnel_label
        self.vc_label = vc_label
        pad = [0, 0, 0, 0, 0, 0]

        body = ''
        for b in self.eth_src:
            body += struct.pack("!B", b)
        for b in self.eth_dst:
            body += struct.pack("!B", b)
        fmt = "!LL"
        body += struct.pack(fmt, self.tunnel_label, self.vc_label)
        fmt = "!BBBBBB"
        body += struct.pack(fmt, pad[0], pad[1], pad[2], pad[3], pad[4], pad[5])

        super(PushL2MPLS, self).__init__(tunnel_type=self.tunnel_type,
                                         flags=self.flags, data=body)

    def show(self):
        """Return a description of the action"""
        desc = super(PushL2MPLS, self).show()
        desc += "\tEth Src: %s\n" % self.eth_src
        desc += "\tEth Dst: %s\n" % self.eth_dst
        desc += "\tTunnel Label: %s\n" % self.tunnel_label
        desc += "\tVC Label: %s\n" % self.vc_label
        return desc


class PopTunnel(parser.OFPActionExperimenter):
    """Pop Tunnel

    uint32 exp_type
    uint8 tunnel_type
    uint8 pad[3]
    """
    def __init__(self, tunnel_type):
        self.exp_type = exp_const.CUSTOMER_NOVIFLOW << 24 | exp_const.RESERVED << 16 | exp_const.NOVI_ACTION_POP_TUNNEL
        if isinstance(tunnel_type, str):
            self.tunnel_type = eval('exp_const.TUNNEL_TYPE_%s' % tunnel_type.upper())
        else:
            self.tunnel_type = tunnel_type
        pad = [0, 0, 0]

        fmt = "!LB"
        body = struct.pack(fmt, self.exp_type, self.tunnel_type)
        fmt = "!BBB"
        body += struct.pack(fmt, pad[0], pad[1], pad[2])

        super(PopTunnel, self).__init__(exp_const.NOVIFLOW_EXPERIMENTER_ID,
                                        data=body)

    def get_action_type(self):
        """Return the experimenter action subtype"""
        return self.exp_type

    def show(self):
        """Return a description of the action"""
        desc = "Experimenter Action: Pop Tunnel\n"
        desc += "\tAction Exp Type: %d (0x%x)\n" % (self.exp_type, self.exp_type)
        desc += "\tTunnel Type: %d\n" % self.tunnel_type
        return desc


# BFD


class SetBfd(parser.OFPActionExperimenter):
    """Activate BFD on the specified port
    This action can be used only in packet_out messages, including in the
    packet_out data the header of the BFD packet to be used on dataplane; this
    header must include the BFD layer, for example Ether/IP/UDP/BFD

    uint32 port_no
    uint32 my_disc
    uint32 interval[us] - minimum accepted value is 100000us [default=100000]
    uint8 multiplier [default=3]
    uint8 pad[6]
    """
    def __init__(self, port_no, my_disc=1, interval=100000, multiplier=3):
        self.exp_type = exp_const.CUSTOMER_NOVIFLOW << 24 | exp_const.RESERVED << 16 | exp_const.NOVI_ACTION_SET_BFD
        self.port_no = port_no
        self.my_disc = my_disc
        self.interval = interval
        self.multiplier = multiplier
        pad = [0, 0, 0, 0, 0, 0, 0, 0]

        fmt = "!LLLLB"
        body = struct.pack(fmt, self.exp_type, self.port_no, self.my_disc,
                           self.interval, self.multiplier)
        fmt = "!BBBBBBB"
        body += struct.pack(fmt, pad[0], pad[1], pad[2], pad[3], pad[4], pad[5], pad[6])

        super(SetBfd, self).__init__(exp_const.NOVIFLOW_EXPERIMENTER_ID,
                                     data=body)

    def get_action_type(self):
        """Return the experimenter action subtype"""
        return self.exp_type

    def show(self):
        """Return a description of the action"""
        desc = "Experimenter Action: Set BFD\n"
        desc += "\tPort No: %d\n" % self.port_no
        desc += "\tMy Discriminator: %d\n" % self.my_disc
        desc += "\tInterval: %dus (%dms)\n" % (self.interval, self.interval)
        desc += "\tMultiplier: %d\n" % self.multiplier
        return desc
