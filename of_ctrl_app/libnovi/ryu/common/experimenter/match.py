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

import yaml
import ryu.ofproto.ofproto_v1_3 as ofp_v13
import ryu.ofproto.ofproto_v1_4 as ofp_v14
import ryu.ofproto.oxm_fields as oxm_fields
from ryu.lib.type_desc import IntDescr

import libnovi.ryu.common.experimenter.const as exp_const

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


class NoviOxmId(parser.OFPOxmId):
    def __init__(self, type_, hasmask=False, length=None, class_=ofproto.OFPXMC_OPENFLOW_BASIC):
        parser.OFPOxmId.__init__(self, "field_%d" % type_, hasmask=False, length=None)
        self.class_ = class_
#         I NEED TO ADD A WAY TO INCLUDE EXPERIMENTER ID IN TABLE FEATURES FOR THIS ONE

    def serialize(self):
        self.length = 0
        (n, _v, _m) = ofproto.oxm_from_user(self.type, None)
        if self.class_ == ofproto.OFPXMC_EXPERIMENTER:
            # Expand header to include experimenter ID
            oxm = self.class_ << 16 | (n << 9) | (self.hasmask << 8) | self.length
            oxm = oxm << 32 | exp_const.NOVIFLOW_EXPERIMENTER_ID
            self._PACK_STR = '!Q'
        else:
            oxm = self.class_ << 16 | (n << 9) | (self.hasmask << 8) | self.length
        buf = bytearray()
        parser.msg_pack_into(self._PACK_STR, buf, 0, oxm)
        return buf


class NoviMatch(parser.OFPMatch):
    def __init__(self, type_=None, length=None, _ordered_fields=None, **kwargs):
        if 'udp_payload' in kwargs:
            _create_payload_oxm('udp_payload', kwargs)
        if 'ip_payload' in kwargs:
            _create_payload_oxm('ip_payload', kwargs)

        super(NoviMatch, self).__init__(type_=type_, length=length, _ordered_fields=_ordered_fields, **kwargs)


class NoviExperimenterMatch(oxm_fields._Experimenter):
    experimenter_id = exp_const.NOVIFLOW_EXPERIMENTER_ID

    def __init__(self, name, num, type_):
        super(NoviExperimenterMatch, self).__init__(name, 0, type_)
        self.num = (exp_const.NOVIFLOW_EXPERIMENTER_ID, num)
        self.oxm_type = num | (self._class << 7)


def _create_payload_oxm(exp_name, exp_dict):
    if isinstance(exp_dict[exp_name], (tuple, list)):
        ByteList = IntDescr(len(exp_dict[exp_name]))
        tmpVal, tmpMask = [], []
        for el in exp_dict[exp_name]:
            if isinstance(el, (tuple, list)):
                tmpVal.append(el[0])
                tmpMask.append(el[1])
            else:
                tmpVal.append(el)
                tmpMask = None
    else:
        ByteList = IntDescr(len(exp_dict[exp_name]))
        tmpVal = exp_dict[exp_name]
        tmpMask = None
    iVal = 0
    iMask = None
    for idx,el in enumerate(tmpVal):
        if isinstance(el, str):
            iVal |= ord(el)<<(8*(len(tmpVal)-idx-1))
        else:
            iVal |= el<<(8*(len(tmpVal)-idx-1))
    if tmpMask is not None:
        iMask = 0
        for idx,el in enumerate(tmpMask):
            if isinstance(el, str):
                iMask |= ord(el)<<(8*(len(tmpMask)-idx-1))
            else:
                iMask |= el<<(8*(len(tmpMask)-idx-1))
    exp_dict[exp_name] = (iVal, iMask)
    parser.ofproto.oxm_types.append(NoviExperimenterMatch(exp_name,
                                    eval('exp_const.NOVI_MATCH_%s' % exp_name.upper()), ByteList))
    parser.ofproto.oxm_fields.generate(parser.ofproto.__name__)

