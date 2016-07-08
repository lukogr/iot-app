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

"""List of all the available URI in NoviRest and the legacy ones from ofctl_rest"""

##########
# LEGACY #
##########
LEGACY = '/stats/'
NOVI = '/novi/'

# PORT
PORT_STATS = LEGACY + 'port/%d'
QUEUE_STATS = LEGACY + 'queue/%d'

# METER
METER_STATS = LEGACY + 'meter/%d'
METER_CONFIG = LEGACY + 'meterconfig/%d'
GROUP_STATS = LEGACY + 'group/%d'
GROUP_DESC = LEGACY + 'groupdesc/%d'


############
# NOVIREST #
############


# GET /novi/novi_rest : Verify if NoviREST App is running
# It returns CODE_SUCCESS if novi_rest.py is running fine
CHECK_NOVIREST_MODULE = NOVI + 'novi_rest'
# GET /novi/switches : Get the list of connected switches DPIDs
DPID_LIST = NOVI + 'dpid_list'


# Controller to Switch

# POST /novi/flow_mod
# params={'n_flows': N_INT}
# data = {'dpid': REQUIRED, 'command': 'add', 'table_id': <table_id>, 'priority': <prio>,
#         'match': {}, 'instructions': []}
FLOW_MOD = NOVI + 'flow_mod'

# POST /novi/group_mod
# data = {'dpid': REQUIRED, 'command': 'add', 'group_id': REQUIRED, 'type': indirect}
GROUP_MOD = NOVI + 'group_mod'

# POST /novi/packet_out
# data = {'dpid': REQUIRED, 'actions': [], 'data': 'string of bytes'
#         'in_port': <in_port>, 'buffer_id': <buffer_id>}
PACKET_OUT = NOVI + 'packet_out'

# PORT /novi/barrier
BARRIER = NOVI + 'barrier'

# Stat

# GET /novi/stats/queue_config : get_queue_config transaction (OF 1.3 only)
QUEUE_CONFIG = NOVI + 'stats/queue_config'

# POST /novi/set_table_features : Change the match fields supported by the table
# data = {'dpid': REQUIRED, 'match_fields': [], 'table_id': ALL}
SET_TABLE_FEATURES = NOVI + 'set_table_features'

# GET /novi/table_featires : Get the description of the table features
GET_TABLE_FEATURES = NOVI + 'get_table_features'


# Experimenter

# POST /novi/udp_payload_config : Configure size and offset for UDP payload matching
# data = {'dpid': REQUIRED, table_id: REQUIRED, 'size': REQUIRED, 'offset': REQUIRED}
UDP_PAYLOAD_CONFIG = NOVI + 'udp_payload_config'

# POST /novi/ip_payload_config : Configure size and offset for IP payload matching
# data = {'dpid': REQUIRED, table_id: REQUIRED, 'size': REQUIRED, 'offset': REQUIRED}
IP_PAYLOAD_CONFIG = NOVI + 'ip_payload_config'
