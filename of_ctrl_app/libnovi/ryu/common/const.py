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

"""Convert OF constant to string"""
import ryu.ofproto.ofproto_v1_3 as ofp

# PORTS
ofp_port_no_map = {
    "OFPP_MAX": ofp.OFPP_MAX,
    "OFPP_IN_PORT": ofp.OFPP_IN_PORT,
    "OFPP_TABLE": ofp.OFPP_TABLE,
    "OFPP_NORMAL": ofp.OFPP_NORMAL,
    "OFPP_FLOOD": ofp.OFPP_FLOOD,
    "OFPP_ALL": ofp.OFPP_ALL,
    "OFPP_CONTROLLER": ofp.OFPP_CONTROLLER,
    "OFPP_LOCAL": ofp.OFPP_LOCAL,
    "OFPP_ANY": ofp.OFPP_ANY,
}
