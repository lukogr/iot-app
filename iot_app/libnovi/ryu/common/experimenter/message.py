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
from libnovi.ryu.common.experimenter.const import CUSTOMER_NOVIFLOW, NOVIFLOW_EXPERIMENTER_ID, RESERVED
from libnovi.ryu.common.experimenter.const import EXP_MSG_UDP_PAYLOAD, EXP_MSG_IP_PAYLOAD


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


class NoviExpMessage(parser.OFPExperimenter):
    """Noviflow Generic Experimenter message

    exp_type formatted following the structure "customer | reserved | msg_type",
    experimenter_id is hardcoded to the value assigned to NoviFlow (0xff000002)"""
    def __init__(self, datapath, exp_subtype, customer_id=CUSTOMER_NOVIFLOW,
                 data=None):
        self.type_ = customer_id << 24 | RESERVED << 16 | exp_subtype
        parser.OFPExperimenter.__init__(self, datapath,
                                        experimenter=NOVIFLOW_EXPERIMENTER_ID,
                                        exp_type=self.type_, data=data)

    def get_exp_subtype(self):
        """Return the NoviFlow specific Experimenter message subtype"""
        return self.type_ & 0xFF

    def get_exp_type(self):
        """Retrun the complete experimenter type"""
        return self.type_


class ConfigUdpPayloadSizeOffset(NoviExpMessage):
    """Message to configure the Offset and Size for UDP payload matching

    This message must be used to configure the desired offset value, and the
    number of Bytes of the UDP payload which will be used for matching"""
    def __init__(self, datapath, table_id, payload_size, payload_offset):
        """Build data and pass it to Ryu's OFPExperimenter message

        :param uint8 table_id: ID of the Table to be configured
        :param uint8 payload_size: Length in Bytes of the portion of UDP payload
            to match on
        :param uint16 payload_offset: Offset in Bytes of the portion of UDP
            payload to match on (0 = no offset, matching on the first Byte of
            the payload)"""
        data = struct.pack("!BBH", table_id, payload_size, payload_offset)
        NoviExpMessage.__init__(self, datapath, EXP_MSG_UDP_PAYLOAD,
                                data=data)


class ConfigIpPayloadSizeOffset(NoviExpMessage):
    """Message to configure the Offset and Size for IP payload matching

    This message must be used to configure the desired offset value, and the
    number of Bytes of the IP payload which will be used for matching"""
    def __init__(self, datapath, table_id, payload_size, payload_offset):
        """Build data and pass it to Ryu's OFPExperimenter message

        :param uint8 table_id: ID of the Table to be configured
        :param uint8 payload_size: Length in Bytes of the portion of IP payload
            to match on
        :param uint16 payload_offset: Offset in Bytes of the portion of IP
            payload to match on (0 = no offset, matching on the first Byte of
            the payload)"""
        data = struct.pack("!BBH", table_id, payload_size, payload_offset)
        NoviExpMessage.__init__(self, datapath, EXP_MSG_IP_PAYLOAD, data=data)
