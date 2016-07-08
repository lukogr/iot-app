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

"""Library of useful functions to build OF messages"""
from scapy.all import Ether
from ryu.lib.mac import haddr_to_str


def eth_int_to_str(iMac):
    """Convert MAC Int into corresponding String"""
    addr = ''
    strMac = str(hex(iMac).lstrip('0x')).rstrip('L')
    while len(strMac) < 12:
        strMac = '0' + strMac
    addr += strMac[0:2] + ":" + strMac[2:4] + ":" + strMac[4:6] + ":" + strMac[6:8] + ":" + strMac[8:10] + ":" + strMac[10:12]
    return addr


def eth_str_to_int(sMac):
    """Convert string MAC address into corresponding Int (to ease incrementation)"""
    s_list = sMac.split(':')
    i_list = [0, 0, 0, 0, 0, 0]
    iMac = 0
    for idx, el in enumerate(s_list):
        i_list[idx] = int(el, 16)
    for idx, el in enumerate(i_list):
        iMac += el << (8 * (5 - idx))
    return iMac


def eth_str_to_list(sMac):
    return [int(el, 16) for el in sMac.split(":")]


def ipv4_int_to_str(iIp):
    """Convert IP Int into corresponding String"""
    tmp = [0, 0, 0, 0]
    for i in range(4):
        tmp[i] = str((iIp >> (8 * (3 - i))) % 256)
    return ".".join(tmp)


def ipv4_str_to_int(sIp):
    """Convert string IP address into corresponding Int (to ease incrementation)"""
    s_list = sIp.split('.')
    iIp = 0
    for idx, el in enumerate(s_list):
        iIp += int(el) << (8 * (3 - idx))
    return iIp


def increment_val(curr_val, range_, step=1):
    """Increment the value by the desired step, and wrap around when the max
    limit of the range is reached"""
    if isinstance(range_, (list, tuple)):
        if curr_val < range_[1]:
            return curr_val + step
        else:
            return range_[0]  # Wrap Around
    else:
        return curr_val


def get_eth_src(msg):
    dp = msg.datapath
    eth_src = None
    for f in msg.match.fields:
        if f.header == dp.ofproto.OXM_OF_ETH_SRC:
            eth_src = haddr_to_str(f.value)
    if eth_src is None:
        eth_src = Ether(str(msg.data)).src
    return eth_src
