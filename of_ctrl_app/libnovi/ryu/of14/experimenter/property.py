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

import sys
import traceback
import struct
import logging
import libnovi.ryu.common.experimenter.const as exp_const

LOG = logging.getLogger('GGGG')


def parse_property(_property):
    """Receives a OFPPropCommonExperimenter4ByteData property, determine
    the corresponding NoviFlow experimenter property and create an object
    describing it propertly

    All these property classes can't be used to create OF messages with Ryu,
    they are only parser for information that Ryu doesn't know how to read."""
    try:
        assert _property.experimenter == exp_const.NOVIFLOW_EXPERIMENTER_ID
        assert _property.exp_type >> 16 == exp_const.CUSTOMER_NOVIFLOW << 8 | exp_const.RESERVED
        subtype = _property.exp_type & 0xFFFF
        assert subtype in exp_subtype_class_map
        retclass = exp_subtype_class_map[subtype](_property.data)
    except (Exception, AssertionError), e:
        LOG.error('Problem parsing experimenter property: %s', e)
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb)
        return None

    return retclass


# Port Description / Port Status


class PortPropBfd(object):
    """BFD property which can be included in port_desc and port_status messages"""
    def __init__(self, data=bytearray()):
        self.experimenter = exp_const.NOVIFLOW_EXPERIMENTER_ID
        self.subtype = exp_const.PORT_DESC_BFD_PROP_TYPE
        self.exp_type = exp_const.CUSTOMER_NOVIFLOW << 24 | exp_const.RESERVED << 16 | self.subtype

        # Convert Byte array to binary string
        binstr = ''
        for el in data:
            binstr += struct.pack("!L", el)
        # Then unpack the binary string
        fmt = "!II"
        start = 0
        end = start + struct.calcsize(fmt)
        (self.my_disc, self.your_disc) = struct.unpack(fmt, binstr[start:end])
        fmt = "!III"
        start = end
        end = start + struct.calcsize(fmt)
        (self.interval_configured, self.tx_interval, self.rx_interval) = struct.unpack(fmt, binstr[start:end])
        fmt = "!BB"
        start = end
        end = start + struct.calcsize(fmt)
        (self.status, self.multiplier) = struct.unpack(fmt, binstr[start:end])
        fmt = "!BBBBBB"
        start = end
        end = start + struct.calcsize(fmt)
        self.peer = ":".join("%02x" % i for i in struct.unpack(fmt, binstr[start:end]))

    def show(self, prefix):
        ret = prefix + "BFD Experimenter property:\n"
        prefix += '    '
        ret += prefix + "Status: %s (%d)\n" % (exp_const.port_desc_bfd_status_map[self.status], self.status)
        ret += prefix + "SW discriminator: %d, Peer discriminator: %d\n" % (self.my_disc, self.your_disc)
        ret += prefix + "Configured interval: %d, Multiplier: %d\n" % (self.interval_configured, self.multiplier)
        ret += prefix + "Tx interval: %d, Rx interval: %d\n" % (self.tx_interval, self.rx_interval)
        ret += prefix + "Peer MAC: %s\n" % (self.peer)
        return ret

exp_subtype_class_map = {
    exp_const.PORT_DESC_BFD_PROP_TYPE: PortPropBfd
}


