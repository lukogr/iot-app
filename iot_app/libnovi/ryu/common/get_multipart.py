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

from ryu.lib.ofctl_v1_3 import send_stats_request


def table_features(dp, waiters):
    parser = dp.ofproto_parser
    stats = parser.OFPTableFeaturesStatsRequest(dp)
    msgs = []
    send_stats_request(dp, stats, waiters, msgs)
    dpid = dp.id
    desc = {dpid: {}}
    if len(msgs) > 0:
        for msg in msgs:
            for s in msg.body:
                desc[dpid][s.table_id] = {}
                desc[dpid][s.table_id]['table_id'] = s.table_id
    desc[dpid]['other'] = 'table_features parsing_incomplete'
    return desc
