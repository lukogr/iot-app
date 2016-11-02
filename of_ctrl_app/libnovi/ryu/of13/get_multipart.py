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
import ryu.ofproto.ofproto_v1_3 as ofp


def queue_config(dp, waiters, port=ofp.OFPP_ANY):
    """Perform get_queue_config transaction and return a dictionary with the
    following structure

    ret = {"<dpid>": {
              "<port_a>": {
                 "port_no": <port_a>,
                 "queues": {
                    "<queue_id>": {"queue_id": <queue_id>,
                                   "port_no": <port_no>,
                                   "min_rate": <min_rate>,
                                   "max_rate": <max_rate>}}}
              "<port_b>": ...

           }}}}}
    """
    parser = dp.ofproto_parser
    stats = parser.OFPQueueGetConfigRequest(dp, port)
    msgs = []
    send_stats_request(dp, stats, waiters, msgs)
    dpid = dp.id
    desc = {dpid: {}}
    if len(msgs) > 0:
        for msg in msgs:
            for stat in msg.queues:
                if stat.port not in desc[dpid].keys():
                    desc[dpid][stat.port] = {'port_no': stat.port, 'queues': {}}
                props = {}
                for p in stat.properties:
                    if p.property == ofp.OFPQT_MIN_RATE:
                        props['min_rate'] = p.rate
                    elif p.property == ofp.OFPQT_MAX_RATE:
                        props['max_rate'] = p.rate
                    else:
                        props['error'] = ['unknown property: %d' % p.property]
                desc[dpid][stat.port]['queues'][stat.queue_id] = {
                    'queue_id': stat.queue_id, 'port_no': stat.port,
                    'properties': props
                }
    return desc
