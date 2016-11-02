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
import logging
import signal
import yaml
import ryu.app.ofctl_rest as ofctl_rest
from ryu.ofproto import ofproto_v1_4, ofproto_v1_3
from webob import Response
import json
import requests

import ryu.controller.ofp_event as ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import CONFIG_DISPATCHER, DEAD_DISPATCHER, MAIN_DISPATCHER

import libnovi.ryu.common.experimenter.message as exp_messages
import libnovi.ryu.common.messages as messages
from libnovi.ryu.common import get_multipart
from libnovi.ryu.of13 import get_multipart as of13_get_multipart
import libnovi.ryu.of14.experimenter.property as of14_exp_prop

import libnovi.ryu.uri as uri

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import udp

#app:
from iot_app_conf import demo_config, channel_type_short, iot_fwd_port
import requests, json, re, time, logging.config, threading
from cherrypy import wsgiserver
from flask import Flask,jsonify, render_template, request, make_response, current_app, redirect
from datetime import timedelta
from functools import update_wrapper


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator
#---------------------------------------------------------#

app = Flask(__name__)

class FlaskAPP(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.active = True
        
        self.d = wsgiserver.WSGIPathInfoDispatcher({'/': app})
        self.server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 5000), self.d)

    def run(self):
        # run flask service:
        print "Starting flask service"
        
        self.server.start()

        while self.active:        
            time.sleep(1)
                        
    def stop(self):        
        print "Flask stopping"
        self.active = False
        #self.server.stop()
        print "Flask stopped"
        

#---------------------------------------------------------#

flask_app = FlaskAPP()
flask_app.start()

#---------------------------------------------------------#

LOG = logging.getLogger(__name__)
log_filename = 'demo.log'
formatter = logging.Formatter('%(asctime)s - %(name)s %(levelname)s - %(message)s')
rh = logging.handlers.RotatingFileHandler(log_filename, maxBytes=200000, backupCount=3)    
rh.setFormatter(formatter) 

@app.route("/")
def root_():     
    return render_template('index.html')

@app.route("/tnc16")
def tnc16():     
    return render_template('tnc16.html')

@app.route("/control_panel")
def control_panel():     
    return render_template('control_panel.html')

@app.route("/ui")
def ui():     
    return render_template('iot-dc/ui/index.html')

@app.route("/get_app_status")
def get_app_status():        
    app_status={}
    for u in demo_config["users"]:
        app_status[u] = {}
        app_status[u]["account_created"] = demo_config["users"][u]["account_created"]
        app_status[u]["lxc_created"] = demo_config["users"][u]["lxc_created"]
        app_status[u]["parser_created"] = demo_config["users"][u]["udp_socket_created"]
        app_status[u]["iot"] = {}

        if demo_config["users"][u]["account_created"]:
            soc=demo_config["users"][u]["service_IP"]+":"+str(demo_config["users"][u]["service_port"])
            app_status[u]["thingspeak_service_ip"] = "http://"+soc

        else:
            app_status[u]["thingspeak_service_ip"] = None

        for ch in demo_config["channels"]:
            if demo_config["channels"][ch]["user"]==u:
                app_status[u]["iot"][ch]={}
                app_status[u]["iot"][ch]["channel_created"] = demo_config["channels"][ch]["channel_created"]
                app_status[u]["iot"][ch]["path_established"] = demo_config["channels"][ch]["path_established"]               


    return jsonify(status=app_status)
    #return jsonify(status=demo_config)

@app.route("/run_gen")
@crossdomain(origin='*')
def run_gen():    
    try: 
        response = requests.get("http://10.0.0.53:5000/rungen")  
        return jsonify(status=response.status_code)
    except:
        return jsonify(status="error during connection to the udp generator")

@app.route("/stop_gen")
@crossdomain(origin='*')
def stop_gen():     
    try: 
        response = requests.get("http://10.0.0.53:5000/stopgen")  
        return jsonify(status=response.status_code)
    except:
        return jsonify(status="error during connection to the udp generator")


with open('config.yaml') as conffile:
    config = yaml.load(conffile)
    if config['ofp_version'] == ofproto_v1_3.OFP_VERSION:
        OFPROTO = ofproto_v1_3
    elif config['ofp_version'] == ofproto_v1_4.OFP_VERSION:
        OFPROTO = ofproto_v1_4
    else:
        print "OF Version %s not supported, using 1.3 Ryu parser. Please Fix config.yaml" % config['ofp_version']
        OFPROTO = ofproto_v1_3


################################################################################
# List of all URIs supported by NoviREST, with related documentation
################################################################################

# Useful
RYU_ADDR = 'http://%s:%d'  # Remember to specify ryu_IP and ryu_port in each request
STATS = '/stats'
NOVI = '/novi'

# GET /novi/empty_error/{dpid}
EMPTY_ERROR = NOVI + '/empty_error/{dpid}'

# Codes
CODE_SUCCESS = 200
CODE_ERROR = 501
CODE_NOT_FOUND = 404
ERROR_RECEIVED = 600

################################################################################
# Controller
################################################################################


def ctrl_c_handler(signal, frame):
    """Catch Ctrl-C and exit App"""
    iot_app.stop()
    
    if flask_app.isAlive():
        flask_app.stop()      
    
    LOG.info("#### Ctrl-C. Exiting Application ####")
    sys.exit(0)


class NoviStatsController(ofctl_rest.StatsController):
    """This Controller's methods are called by the REST API"""
    def __init__(self, req, link, data, **config):
        self.features = data['features']
        super(NoviStatsController, self).__init__(req, link, data, **config)
        self.app_ref = data['main_app']

    def _eval_syntax(self, req):
        """Evaluate syntax of request body, to ensure that it can be loaded by json"""
        try:
            msg = eval(req.body)
            return msg
        except SyntaxError, e:
            err_msg = 'invalid syntax %s (%s)' % (e, req.body)
            LOG.debug(err_msg)
            return Response(body=err_msg, status=CODE_ERROR)

    def _validate_dpid(self, dpid):
        """Verify that specified DPID corresponds to a connected Switch"""
        dp = self.dpset.get(int(dpid))
        if dp is None:
            err_msg = "Invalid DPID: no Switch with DPID %s (0x%x) connected" % (dpid, int(dpid))
            LOG.debug(err_msg)
            return Response(status=CODE_ERROR, body=err_msg)
        return dp

    def _validate_required(self, msg_type, required, keys):
        """Verify that all required dictionary keys are present in req.data"""
        for el in required:
            assert el in keys, "%s must be specified in %s message dictionary" % (el, msg_type)

    def module_present(self, req, **_kwargs):
        """If this App is running, this will return a success code"""
        return Response(status=CODE_SUCCESS, body="Novi REST is running")

    def get_dpids_addr(self, req, **_kwargs):
        """Create a dict with DPID: Address items for all connected switches"""
        switches = {}
        for d in self.dpset.dps:
            switches[d] = self.dpset.get(int(d)).address[0]
        body = json.dumps(switches)
        return (Response(content_type='application/json', body=body))

    def flow_mod(self, req, **_kwargs):
        """Verify that the request's body include the required info to be used
        by the method which will create and send the flow_mod OF message"""
        flow = self._eval_syntax(req)
        dp = self._validate_dpid(flow.get('dpid'))
        # If n_flows is passed as URI parameter, add it to dict passed to flow_mod method
        try:
            if 'n_flows' in req.params:
                flow['n_flows'] = int(req.params['n_flows'])
        except Exception, e:
            err_msg = "Problem parsing request's parameters (%s)" % e
            LOG.debug(err_msg)
            return Response(body=err_msg, status=CODE_ERROR)
        messages.flow_mod(dp, flow)

        return Response(status=CODE_SUCCESS)

    def group_mod(self, req, **_kwargs):
        """Verify that the request's body include the required info to be used
        by the method which will create and send the group_mod OF message"""
        group = self._eval_syntax(req)
        dp = self._validate_dpid(group.get('dpid'))
        dp.send_msg(messages.group_mod(dp, group))

        return Response(status=200)

    def packet_out(self, req, **_kwargs):
        """Verify that the request's body include the required info to be used
        by the method which will create and send the packet_out OF message"""
        pout = self._eval_syntax(req)
        dp = self._validate_dpid(pout.get('dpid'))
        dp.send_msg(messages.packet_out(dp, pout))

        return Response(status=200)

    def set_table_features(self, req, **_kwargs):
        """Verify that the request's body include the required info to be used
        by the method which will create and send the table_features OF message"""
        feat = self._eval_syntax(req)
        # DPID
        dpid = feat.get('dpid')
        dp = self._validate_dpid(dpid)
        # Check that required parameters are passed in dict
        required = ['match_fields']
        for el in required:
            assert el in feat.keys(), "%s must be specified in table_features message" % el
        # Table ID, if not specifies use OFPTT_ALL
        try:
            n_tables = int(self.features[dpid]['n_tables'])
            tab_id = feat.get('table_id', dp.ofproto.OFPTT_ALL)
            matches = feat.get('match_fields')
        except Exception, e:
            err_msg = "Problem parsing values: %s" % e
            LOG.debug(err_msg)
            return Response(status=404, body=err_msg)

        dp.send_msg(messages.table_features(dp, n_tables,
                                            table_id=tab_id, match_list=matches))
        dp.send_msg(dp.ofproto_parser.OFPBarrierRequest(dp))

        return Response(status=200)

    def barrier(self, req, **_kwargs):
        """Sends a barrier_request"""
        content = self._eval_syntax(req)
        dp = self._validate_dpid(content.get('dpid'))
        dp.send_msg(dp.ofproto_parser.OFPBarrierRequest(dp))
        return Response(status=200)

    def udp_payload_config(self, req, **_kwargs):
        """Verify that the request's body include the required info to be used
        by the method which will create and send the experimenter OF message
        to configure the UDP payload match size and offset"""
        config = self._eval_syntax(req)
        # DPID
        dpid = config.get('dpid')
        dp = self._validate_dpid(dpid)
        # Check all required parameters
        self._validate_required('experimenter_udp_config', ['size', 'offset', 'table_id'], config.keys())
        # Parse arguments
        try:
            config_size = int(config.get('size'))
            config_offset = int(config.get('offset'))
            config_table = int(config.get('table_id'))
        except Exception, e:
            err_msg = "Problem parsing values: %s" % e
            LOG.debug(err_msg)
            return Response(status=404, body=err_msg)
        # Send message
        dp.send_msg(exp_messages.ConfigUdpPayloadSizeOffset(dp, config_table, config_size, config_offset))
        dp.send_msg(dp.ofproto_parser.OFPBarrierRequest(dp))

        return Response(status=200)

    def ip_payload_config(self, req, **_kwargs):
        """Verify that the request's body include the required info to be used
        by the method which will create and send the experimenter OF message
        to configure the IP payload match size and offset"""
        config = self._eval_syntax(req)
        # DPID
        dpid = config.get('dpid')
        dp = self._validate_dpid(dpid)
        self._validate_required('experimenter_ip_config', ['size', 'offset', 'table_id'], config.keys())
        # Parse arguments
        try:
            config_size = int(config.get('size'))
            config_offset = int(config.get('offset'))
            config_table = int(config.get('table_id'))
        except Exception, e:
            err_msg = "Problem parsing values: %s" % e
            LOG.debug(err_msg)
            return Response(status=404, body=err_msg)
        # Send message
        dp.send_msg(exp_messages.ConfigIpPayloadSizeOffset(dp, config_table, config_size, config_offset))
        dp.send_msg(dp.ofproto_parser.OFPBarrierRequest(dp))

        return Response(status=200)

    def get_queue_config(self, req, **_kwargs):
        config = self._eval_syntax(req)
        dpid = config.get('dpid')
        dp = self._validate_dpid(dpid)
        port = config.get('port', dp.ofproto.OFPP_ANY)

        if dp.ofproto.OFP_VERSION == ofproto_v1_3.OFP_VERSION:
            queues = of13_get_multipart.queue_config(dp, self.waiters, port)
        else:
            LOG.debug('Request not supported in this OF protocol version (%d)'
                      % dp.ofproto.OFP_VERSION)
            return Response(status=CODE_ERROR)

        body = json.dumps(queues)
        return (Response(content_type='application/json', body=body))

    def get_table_features(self, req, **_kwargs):
        config = self._eval_syntax(req)
        dpid = config.get('dpid')
        dp = self._validate_dpid(dpid)
        tables = get_multipart.table_features(dp, self.waiters)

        body = json.dumps(tables)
        return (Response(content_type='application/json', body=body))

    def empty_error_queue(self, req, dpid, **_kwargs):
        """Empty the list of errors received by Ryu"""
        if int(dpid) in self.dpset.dps.keys():
            self.app_ref.emtpy_error_queue(int(dpid))
        return Response()


################################################################################
# REST API
################################################################################

class NoviRestStatsApi(ofctl_rest.RestStatsApi):
    """RESTful API server"""
    OFP_VERSIONS = [OFPROTO.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(NoviRestStatsApi, self).__init__(*args, **kwargs)
        self.features = {}
        self.errors = {}
        self.async = {}
        self.data['features'] = self.features
        self.data['main_app'] = self
        self.wsgi = kwargs['wsgi']
        self.mapper = self.wsgi.mapper
        signal.signal(signal.SIGINT, ctrl_c_handler)

        self.wsgi.registory['NoviStatsController'] = self.data

        # Connect URIs to related functions
        self.mapper.connect('check_module', uri.CHECK_NOVIREST_MODULE,
                            controller=NoviStatsController, action='module_present',
                            conditions=dict(method=['GET']))

        self.mapper.connect('list_switches', uri.DPID_LIST,
                            controller=NoviStatsController, action='get_dpids_addr',
                            conditions=dict(method=['GET']))

        self.mapper.connect('empty_errors', EMPTY_ERROR,
                            controller=NoviStatsController, action='empty_error_queue',
                            conditions=dict(method=['GET']))

        self.mapper.connect('flow_mod', uri.FLOW_MOD,
                            controller=NoviStatsController, action='flow_mod',
                            conditions=dict(method=['POST']))

        self.mapper.connect('group_mod', uri.GROUP_MOD,
                            controller=NoviStatsController, action='group_mod',
                            conditions=dict(method=['POST']))

        self.mapper.connect('packet_out', uri.PACKET_OUT,
                            controller=NoviStatsController, action='packet_out',
                            conditions=dict(method=['POST']))

        self.mapper.connect('change_table_features', uri.SET_TABLE_FEATURES,
                            controller=NoviStatsController, action='set_table_features',
                            conditions=dict(method=['POST']))

        self.mapper.connect('udp_payload_configuration', uri.UDP_PAYLOAD_CONFIG,
                            controller=NoviStatsController, action='udp_payload_config',
                            conditions=dict(method=['POST']))

        self.mapper.connect('ip_payload_configuration', uri.IP_PAYLOAD_CONFIG,
                            controller=NoviStatsController, action='ip_payload_config',
                            conditions=dict(method=['POST']))

        self.mapper.connect('barrier', uri.BARRIER,
                            controller=NoviStatsController, action='barrier',
                            conditions=dict(method=['POST']))

        # STATS and CONFIG
        self.mapper.connect('get_table_features', uri.GET_TABLE_FEATURES,
                            controller=NoviStatsController, action='get_table_features',
                            conditions=dict(method=['GET']))

        # Get queue config message has been removed in OF1.4
        if OFPROTO.OFP_VERSION == ofproto_v1_3.OFP_VERSION:
            self.mapper.connect('get_queue_config', uri.QUEUE_CONFIG,
                                controller=NoviStatsController, action='get_queue_config',
                                conditions=dict(method=['GET']))


        self.logger.addHandler(rh)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Save features of each connected switch"""
        dpid = ev.msg.datapath_id
        self.features[dpid] = {'n_tables': ev.msg.n_tables,
                               'n_buffers': ev.msg.n_buffers,
                               'auxiliary_id': ev.msg.auxiliary_id,
                               'capabilities': ev.msg.capabilities}
        self.async[dpid] = {'description': [],
                            'flow_stats': [],
                            'aggregate_stats': [],
                            'table_stats': [],
                            'table_features': [],
                            'port_stats': [],
                            'port_desc': [],
                            'queue_stats': [],
                            'group_stats': [],
                            'group_desc': [],
                            'group_features': [],
                            'meter_stats': [],
                            'meter_config': [],
                            'meter_features': [],
                            'experimenter': [],
                            'queue_config': [],
                            'packet_in': [],
                            'role': [],
                            'barrier': [],
                            'async_config': []}
        self.errors[dpid] = []
        self.waiters[dpid] = {}
        self.logger.info("Established connection with datapath ID: 0x%x"
                         % ev.msg.datapath_id)

        ev.msg.datapath.send_msg(ev.msg.datapath.ofproto_parser.OFPDescStatsRequest(ev.msg.datapath, 0))

        # for demo:
        iot_app.configureNoviForDemo(ev)


    @set_ev_cls(ofp_event.EventOFPStateChange, DEAD_DISPATCHER)
    def switch_disconnected(self, ev):
        self.logger.info("Connection lost with DPID 0x%x" % (ev.datapath.id))

    @set_ev_cls(ofp_event.EventOFPQueueGetConfigReply, MAIN_DISPATCHER)
    def queue_config_handler(self, ev):
        # Handle Get Queue Config reply to put it in the corresponding waiter if any
        dp = ev.msg.datapath
        if ev.msg.xid in self.waiters[dp.id]:
            lock, msgs = self.waiters[dp.id][ev.msg.xid]
            msgs.append(ev.msg)
            lock.set()

    @set_ev_cls(ofp_event.EventOFPTableFeaturesStatsReply, MAIN_DISPATCHER)
    def table_features_handler(self, ev):
        dp = ev.msg.datapath
        if ev.msg.xid in self.waiters[dp.id]:
            lock, msgs = self.waiters[dp.id][ev.msg.xid]
            msgs.append(ev.msg)
            lock.set()

    def emtpy_error_queue(self, dpid):
        self.errors[dpid] = []

    @set_ev_cls(ofp_event.EventOFPErrorMsg, MAIN_DISPATCHER)
    def error_handler(self, ev):
        dp = ev.msg.datapath
        if len(self.errors) > MAX_N_ERRORS:
            self.errors.pop(0)
        self.errors[dp.id].append({'code': ev.msg.code, 'type': ev.msg.type,
                                   'data': ev.msg.data})

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        dp = ev.msg.datapath
        port = ev.msg.desc
        if dp.ofproto.OFP_VERSION == ofproto_v1_4.OFP_VERSION:
            eth_prop = port.properties[0]
            self.logger.info("Port Status received from dpid %d" % dp.id)
            self.logger.info("\tPort No: %d (%s)\n\tState: %d\n\tConfig: 0x%x" % (port.port_no, port.name, port.state, port.config))
            self.logger.info("\tCurrent: 0x%x\n\tAdvertised: 0x%x" % (eth_prop.curr, eth_prop.advertised))
            self.logger.info("\tSupported: 0x%x\n\tPeer: 0x%x" % (eth_prop.supported, eth_prop.peer))
            self.logger.info("\tCurr Speed: %d\n\tMax Speed: %d" % (eth_prop.curr_speed, eth_prop.max_speed))

            if len(port.properties) > 1:
                for prop in port.properties[1:]:
                    ret = of14_exp_prop.parse_property(prop)
                    if ret is not None:
                        self.logger.info(ret.show('\t'))
        else:
            self.logger.info("Port Status received from dpid %d" % dp.id)
            self.logger.info("\tPort No: %d (%s)\n\tState: %d\n\tConfig: 0x%x" % (port.port_no, port.name, port.state, port.config))
            self.logger.info("\tCurrent: 0x%x\n\tAdvertised: 0x%x" % (port.curr, port.advertised))
            self.logger.info("\tSupported: 0x%x\n\tPeer: 0x%x" % (port.supported, port.peer))
            self.logger.info("\tCurr Speed: %d\n\tMax Speed: %d" % (port.curr_speed, port.max_speed))

    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        
        iot_app.addEvent(ev)

# --- IoT App ------------------------------------------

class IoTApp(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.active = True
        self.mac_to_port = {}
        self.event_list = []        
        self.channels_created =[]

        self.logger = logging.getLogger('IoTApp')
        self.logger.addHandler(rh)      
        

    
    def configureNoviForDemo(self, ev):
 
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id

        if dpid in demo_config["NoviSwitches"]:

            self.logger.info("Configuring %s (dpid: %s) for the demo "%(demo_config["NoviSwitches"][dpid], dpid))
            time.sleep(3)
            self.logger.info("wait a while..")
            ryu_uri ="http://0.0.0.0:8080"

            self.logger.info("Configure match fields in table 0 ti support IP and UDP payload")
            tf = {'dpid': dpid, 'table_id': 0,
                  'match_fields': ['in_port', 'udp_payload']}        
            requests.post(ryu_uri+(uri.SET_TABLE_FEATURES), data=json.dumps(tf)).text
            
            # Configure UDP payload match size and offset
            self.logger.info("Configure UDP payload match size and offset")
            udp_config = {'dpid': dpid, 'table_id': 0, 'size': 9, 'offset': 26}
            requests.post(ryu_uri+(uri.UDP_PAYLOAD_CONFIG), data=json.dumps(udp_config)).text
            
            self.logger.info("Adding OFPP_CONTROLLER flow modes [for packet_in])")        
            for path in demo_config["network_maps"]: 
                if dpid in demo_config["network_maps"][path]:     
                    for pair in demo_config["network_maps"][path][dpid]["flows"]:
                        ports = [pair["in_port"], pair["out_port"]]

                        for port in ports:
                            match = parser.OFPMatch(in_port=port)
                            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]   
                            self.add_flow(datapath, 100, match, actions) 
                            self.logger.info("Flow mode added for dpid: %s, port: %s"%(dpid,port))
        else:
            self.logger.error("No dpid: %s in the configuration "%(dpid))

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)        

    def signUpUser(self, service_IP, service_port, login, mail, password, time_zone):
        s = requests.session()
        try:
            r = s.get("http://"+service_IP+":"+str(service_port)+"/users/sign_up",verify = False)
        except:
            return 0

        matchme = 'meta content="(.*)" name="csrf-token" /'
        csrf = re.search(matchme,str(r.text))
        authenticity_token = csrf.group(1)
        #self.logger.info( "authenticity_token: %s"%(authenticity_token))

        payload = {
            "authenticity_token": authenticity_token,
            "commit":"Create Account",
            "user[email]":mail,
            "user[login]":login,
            "user[password]":password,
            "user[password_confirmation]":password,
            "user[time_zone]":time_zone,
            "userlogin":None 
        }
        r = s.post("http://"+service_IP+":"+str(service_port)+"/users",data=payload,verify = False)
        #self.logger.info("signUpUser response: %s"%(r.status_code))

        if r.status_code==200:
            time.sleep(3)
            #---account
            payload = {
                "authenticity_token": authenticity_token
            }
            r = s.get("http://"+service_IP+":"+str(service_port)+"/account",data=payload,verify = False)
            matchme = '<code>(.*)</code>'
            APIkey = re.search(matchme,str(r.text))
            ak=APIkey.group(1)
            #self.logger.info("API key: %s"%(ak))
            #---get user id
            payload = {
                "api_key":ak,
            }
            r = requests.get("http://"+service_IP+":"+str(service_port)+"/users/"+login+".json",data=payload,verify = False)
            r_json = r.json()

            return {"ak":ak, "id":r_json["id"]}
        else:
            return 0

    def delUser(self, service_IP, service_port, login, password):
        #login
        s = requests.session()
        try:
            r = s.get("http://"+service_IP+":"+str(service_port)+"/login",verify = False)
        except:
            self.logger.error("No connection with thingspeak service")
            return 0

        matchme = 'meta content="(.*)" name="csrf-token" /'
        csrf = re.search(matchme,str(r.text))
        authenticity_token = csrf.group(1)
        #self.logger.info("authenticity_token: %s"%(authenticity_token))
        #singin
        payload = {
            "authenticity_token": authenticity_token,
            "commit":"Sign In",
            "userlogin": None,
            "user[login]":login,
            "user[password]":password,
            "user[remember_me]":0,
            "user[remember_me]":1
        }
        r = s.post("http://"+service_IP+":"+str(service_port)+"/users/sign_in",data=payload,verify = True)
        #self.logger.info("sing_in response: %s"%(r.status_code))
        
        #---account
        time.sleep(3)
        payload = {
            "authenticity_token": authenticity_token
        }
        r = s.get("http://"+service_IP+":"+str(service_port)+"/account",data=payload,verify = False)
        matchme = '<code>(.*)</code>'
        APIkey = re.search(matchme,str(r.text))
        if APIkey == None:
            self.logger.info("Probably no account for user: %s"%(login))
            return 0
        else:    
            ak=APIkey.group(1)
            print "API key: %s"%(ak)
            #---get user id
            payload = {
                "api_key":ak,
            }
            r = requests.get("http://"+service_IP+":"+str(service_port)+"/users/"+login+".json",data=payload,verify = False)
            r_json = r.json()

            id = r_json["id"]

            #edit account
            r = s.get("http://"+service_IP+":"+str(service_port)+"/account/edit",verify = False)
            matchme = 'meta content="(.*)" name="csrf-token" /'
            csrf = re.search(matchme,str(r.text))
            authenticity_token = csrf.group(1)
            #self.logger.info("authenticity_token: %s"%(authenticity_token))
            #del user
            payload = {
                "authenticity_token": authenticity_token,
                "_method":"delete",
            }
            r = s.post("http://"+service_IP+":"+str(service_port)+"/users/"+str(id),data=payload,verify = True)
            #self.logger.info("delUser response: %s"%(r.status_code))
            return r.status_code

    def createThingSpeakChannel(self, service_IP, service_port, type, ak):
        
        if type=="SmartCity":
            payload = {
                "name": "Smart City channel",
                "api_key":ak,
                "public_flag":"true",
                "description":"Live demonstration",
                "field1":"bat",
                "field2":"temperature",
                "field3":"noise",
                "field4":"ultrasound",
                "field5":"luminocity"    
            }
        if type=="Ambient":
            payload = {
                "name": "Ambient channel",
                "api_key":ak,
                "public_flag":"true",
                "description":"Live demonstration",
                "field1":"bat",
                "field2":"humidity",
                "field3":"luminocity",
                "field4":"lux"  
            }
        if type=="TestChannel":
            payload = {
                "name": "Test channel",
                "api_key":ak,
                "public_flag":"true",
                "description":"Live demonstration",
                "field1":"random"
            }        
        if type=="SpirentChannel":
            payload = {
                "name": "Spirent channel",
                "api_key":ak,
                "public_flag":"true",
                "description":"Live demonstration",
                "field1":"random"
            }        
        header = {'content-type': 'application/json'}
        
        try:
            response = requests.post("http://"+service_IP+":"+str(service_port)+"/channels.json", headers=header, 
                        data=json.dumps(payload))  
            
            
            # update information about "channel location"
            if type=="TestChannel" or type=="SpirentChannel":
                payload_up = {
                    "api_key":ak,
                    
                    #Prague, Venue
                    #"latitude" :"50.109569",
                    #"longitude":"14.501408",
                    
                    #cbpio , 
                    "latitude" :"52.406986",
                    "longitude":"16.953339",
                    
                    "elevation":"0"
                }        
          
                try:
                    requests.put("http://"+service_IP+":"+str(service_port)+"/channels/1", headers=header, 
                                data=json.dumps(payload_up))  
                    
                except:
                    return 0

            return response

        except:
            return 0

    def addEvent(self, ev):
        self.event_list.append(ev)

    def sendPacketOutUDP(self, msg, out_port, wasp_mote_ID):
        self.logger.info("Sending packet_out for UDP packet (dpid: %s | out_port: %s)"%(msg.datapath.id, out_port))
        
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']        

        ak_write = demo_config["channels"][wasp_mote_ID]["ak"]
        user_name =  demo_config["channels"][wasp_mote_ID]["user"]
        service_port = demo_config["users"][user_name]["service_port"]
        channel_type =  demo_config["channels"][wasp_mote_ID]["type"]

        if ak_write != None:
            ins_udp_payload = "#"+channel_type_short[channel_type]+"#" + ak_write + "#"+str(service_port)                                                                 
                                                 
            actions = [parser.OFPActionOutput(out_port)]
            data = None
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data
            index_ = data.index("#"+wasp_mote_ID)
            checksum = "\x00\x00"
            pre = data[0:index_-27]
            post=data[index_::]
            data_out = pre+checksum+str(ins_udp_payload)+post
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                      in_port=in_port, actions=actions, data=data_out)
            datapath.send_msg(out)

                                                                
        else:
            self.logger.warning("AK is not known for %s!"%(wasp_mote_ID))          


    def handleEvents(self):
        self.logger.info("Event handler working | %s events on the list..."%(len(self.event_list)))

        for ev in self.event_list:
            
            msg = ev.msg
            datapath = msg.datapath
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            in_port = msg.match['in_port']
            pkt = packet.Packet(msg.data)
            eth = pkt.get_protocols(ethernet.ethernet)[0]
            dst = eth.dst
            src = eth.src
            dpid = datapath.id
         
            self.logger.info("packet_in dpid:%s src:%s dst:%s in_port:%s", dpid, src, dst, in_port) 
              


            for item in pkt:          
                
                if "udp" == item.__class__.__name__:
                    self.logger.info("### UDP handler ###")  
                    self.logger.info(item)

                    if item.dst_port == 67:
                        self.logger.info("DHCP udp packet - do nothing")
                        continue
                    
                    #for demo:
                    if (item.dst_port != 5555)and(item.dst_port != 7777)and(item.dst_port != 8888):
                        self.logger.info("packet not supported - do nothing")
                        continue                                    

                    ryu_uri ="http://0.0.0.0:8080"

                    wasp_mote_ID = pkt[3][26:35]
                    
                    #check id wasp_mote_ID is supported
                    if wasp_mote_ID in demo_config["channels"]:

                        self.logger.info("%s"%(pkt))
                                                
                        # wasp_mote -> user_name
                        user_name =  demo_config["channels"][wasp_mote_ID]["user"]
                        self.logger.info("^^^ Received new UDP traffic from wasp_mote_ID: %s (Traffic of user: %s)"%(wasp_mote_ID, user_name))
                        
                        service_port = demo_config["users"][user_name]["service_port"]
                        channel_type =  demo_config["channels"][wasp_mote_ID]["type"]
                        
                        #where to send the packet
                        out_port=None
                        path = demo_config["users"][user_name]["map"]                    
                        if dpid in demo_config["network_maps"][path]:
                            for pair in demo_config["network_maps"][path][dpid]["flows"]:
                                if pair["in_port"]==in_port:
                                    out_port = pair["out_port"]
                                    break
                        

                        if out_port != None:
                        
                            if (wasp_mote_ID in self.channels_created) and (demo_config["channels"][wasp_mote_ID]["path_established"]):

                                #just send packet_out (for enqued packets)
                                self.sendPacketOutUDP(msg, out_port, wasp_mote_ID)
                                time.sleep(0.5) # no at once! 

                                
                            else:
                                #--------------------------------------------------------------------------------                               
                                service_IP = demo_config["users"][user_name]["service_IP"]                
                                if not demo_config["users"][user_name]['account_created']: 
                                    

                                    # 1. create container for the user
                                    # 2. run thingspeak service
                                    # 3. redirect traffic from service_IP:service_port to lxd_machine_ip:3000
                                    try:
                                        
                                        #launch container
                                        response_run = requests.get("http://"+service_IP+":"+str(iot_fwd_port)+"/lxc_run/thingspeak-"+user_name)  
                                        self.logger.info("LXC container creation status: %s"%(response_run.json()))
                                        container_ip = None
                                        while container_ip == None:
                                            self.logger.info("Waiting for container IP address...")
                                            response = requests.get("http://"+service_IP+":"+str(iot_fwd_port)+"/lxc_list/thingspeak-"+user_name)  
                                            response_j = response.json()
                                            self.logger.info("%s"%response_j)
                                            if response_j["status"] == "Running":

                                                demo_config["users"][user_name]["lxc_created"] = True
                                                container_ip = response_j["ip"]

                                                #run_script to launch thingspeak
                                                response_script = requests.get("http://"+service_IP+":"+str(iot_fwd_port)+"/lxc_script/thingspeak-"+user_name)  
                                                self.logger.info("response_script: %s"%(response_script))


                                                #redirect
                                                red_res = requests.get("http://"+service_IP+":"+str(iot_fwd_port)+"/port_redirect/"+"\""+service_IP+"&"+str(service_port)+"&"+container_ip+"&3000\"")
                                                self.logger.info("Redirection status: %s"%red_res.json())

    

                                                self.logger.info("Container running under ip: %s"%(container_ip))
                                                
                                            time.sleep(1)

                                    except:
                                        self.logger.error("Problem with LXC container creation")


                                    # ----
                                    user_mail = demo_config["users"][user_name]["mail"]
                                    user_pass = demo_config["users"][user_name]["password"]
                                    time_zone = demo_config["users"][user_name]["time_zone"]    
                                    
                                    #---del user account (if any old exist in thingspeak):
                                    self.logger.info("Delate account: %s (if any old exist)"%(user_name))
                                    self.delUser(service_IP, service_port, user_name, user_pass)

                                    #---account creation:
                                    self.logger.info("Creating new account for: %s, %s, %s, %s, %s, %s"%(service_IP, service_port, user_name, user_mail, user_pass, time_zone))
                                    signUpUser_response = self.signUpUser(service_IP, service_port, user_name, user_mail, user_pass, time_zone)                      

                                    if signUpUser_response != 0:
                                        demo_config["users"][user_name]['account_created'] = True
                                        demo_config["users"][user_name]["APIkey"] = signUpUser_response["ak"]
                                        demo_config["users"][user_name]["ID"] = signUpUser_response["id"]

                                        self.logger.info("Account for user %s created: %s"%(user_name, signUpUser_response))
                                    else:                            
                                        self.logger.error("Something wrong during account creation for user: %s !"%(user_name))
                                else:
                                    self.logger.info("Account for user %s just created. Do nothing."%(user_name))
                                #--------------------------------------------------------------------------------


                                #---create thingspeak channel---
                                if not demo_config["channels"][wasp_mote_ID]["channel_created"]:
                                    self.logger.info("Creating thingspeak channel for wasp_mote: %s"%(wasp_mote_ID))                       
                                    ak = demo_config["users"][user_name]["APIkey"]
                                    response_create_channel = self.createThingSpeakChannel(service_IP, service_port, channel_type,ak)
                                   
                                    if response_create_channel != 0:
                                        if  response_create_channel.status_code == 200:
                                            demo_config["channels"][wasp_mote_ID]["channel_created"] = True     
                                            response_create_channel_j = response_create_channel.json()
                                            demo_config["channels"][wasp_mote_ID]["ak"] = response_create_channel_j["api_keys"][0]["api_key"]

                                            self.logger.info("Channel for wasp_mote: %s created;"%(wasp_mote_ID))

                                            self.channels_created.append(wasp_mote_ID)
                                        else:
                                            self.logger.error("Channel for wasp_mote: %s NOT created (response: %s);"%(wasp_mote_ID, response_create_channel))
                                    else:
                                        self.logger.error("Something wrong during channel creation of thingspeak service!")

                                else:
                                    self.logger.info("Channel for wasp_mote: %s just created. Do NOTHING"%(wasp_mote_ID))
                                #----------------------------

             
                                iot_server_IP = demo_config["users"][user_name]["iot_server_IP"]
                                iot_server_port = demo_config["users"][user_name]["iot_server_port"] 
                                
                                #--- if channels created open UDP sockets and configure OF network
                                # also send packet_out
                                if (demo_config["users"][user_name]['account_created']
                                    and demo_config["channels"][wasp_mote_ID]["channel_created"]):
                                    
                                    if not demo_config["users"][user_name]["udp_socket_created"]:
                                        #--- open UDP socket on iot_server (iot_fwd)
                                        self.logger.info("Opening UDP socket on iot_server")
                                        try:        

                                            #get from flask service
                                            response = requests.get("http://"+service_IP+":"+str(iot_fwd_port)+"/create_udp_socket/\""+iot_server_IP+"&"+str(iot_server_port)+"\"")  
                                            r_json = response.json()
                                            self.logger.info("Open UDP socket response: %s"%(r_json["status"]))
                                            if r_json["status"] == "ok":
                                                demo_config["users"][user_name]["udp_socket_created"] = True

                                        except:
                                            self.logger.error("Some problem during socket opening!")


                                    if not demo_config["channels"][wasp_mote_ID]["path_established"]:
                                        #--- create path in SDN network and send packet_out:

                                        # Install flow_mod into all OF SWs once:
                                                          
                                        for dpid in demo_config["network_maps"][path]:
                                        
                                            self.logger.info("Adding flow_mods to use match and set UDP and IP payload (dpid: %s)"%(dpid))
                                            ak_write = demo_config["channels"][wasp_mote_ID]["ak"]
                                            if ak_write!=None:
                                                
                                                ins_udp_payload = "#"+channel_type_short[channel_type]+"#" + ak_write + "#"+str(service_port)


                                                out_port_action = demo_config["network_maps"][path][dpid]["flows"][0]["out_port"]

                                                # Flow Mod matching on UDP payload 
                                                fm = {'dpid': dpid, 'command': 'add', 'table_id': 0,  'priority': 200,
                                                      'cookie': 1, 'match': {'udp_payload': wasp_mote_ID}, 
                                                       'instructions': [{'type': 'apply',
                                                                        'actions': [  
                                                                            {'type': 'set_field', 'field': 'udp_dst', 'value': iot_server_port},
                                                                            {'type': 'set_field', 'field': 'ipv4_src', 'value': demo_config["users"][user_name]["src_ip"]},
                                                                            {'type': 'set_field', 'field': 'ipv4_dst', 'value': iot_server_IP},
                                                                            {'type': 'experimenter', 'exp_type': 'set_udp_payload', 'offset': 0, 'value': ins_udp_payload},
                                                                            {'type': 'output', 'port': out_port_action}]}]}

                                                                            
                                                requests.post(ryu_uri+(uri.FLOW_MOD), data=json.dumps(fm)).text
             

                                            else:
                                                self.logger.warning("AK is not known for %s!"%(wasp_mote_ID))  

                                        demo_config["channels"][wasp_mote_ID]["path_established"] = True
                                        self.logger.info("E2E path established for ID: %s"%(wasp_mote_ID)) 


                                    # --- send packet_out    
                                    self.sendPacketOutUDP(msg, out_port, wasp_mote_ID)                              
                                         
                                else:
                                    self.logger.warning("Account for %s and channel: %s not created"%(user_name, wasp_mote_ID))     
                                #--------------------------------------------------------------------------------
     
                        else:
                            self.logger.error("out_port for dpid: %s and in_port: %s not configured"%(dpid, in_port))    

                    else:
                        self.logger.error("Received new UDP traffic from UNSUPPORTED wasp_mote_ID: %s",wasp_mote_ID)

                  

                if ("arp" == item.__class__.__name__)or("icmp"== item.__class__.__name__):

                    self.logger.info("### ARP / ICMP ###")      
                    #self.logger.info(item)
                    self.mac_to_port.setdefault(dpid, {})

                    # learn a mac address to avoid FLOOD next time.
                    self.mac_to_port[dpid][src] = in_port

                    self.logger.info("mac_to_port: %s", self.mac_to_port);

                    if dst in self.mac_to_port[dpid]:
                        out_port = self.mac_to_port[dpid][dst]
                    else:
                        out_port = ofproto.OFPP_FLOOD

                    actions = [parser.OFPActionOutput(out_port)]


                    data = None
                    if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                        data = msg.data

                    out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                              in_port=in_port, actions=actions, data=data)
                    datapath.send_msg(out)        
                else:
                    self.logger.info("### unknown frame - not supported ###") 

            self.event_list.remove(ev)

            self.logger.info( "---")
            

    def run(self):
        # run IoT APP
        print "Starting IoTApp..."
        
        try:
            #del if any container exists:
            self.logger.info("Deleting containers (if any exists)...")
            for user in demo_config["users"]:
                service_IP = demo_config["users"][user]["service_IP"]   
                res = requests.get("http://"+service_IP+":"+str(iot_fwd_port)+"/lxc_del/thingspeak-"+user)   
                self.logger.info("User: %s | delete status: %s"%(user, res.status_code))
        except: 
            self.logger.error("Problem with deleting old containers. Check if iot_fwd is running!") 
            self.stop()   
            
                
        while self.active:  

            if len(self.event_list) > 0:
                self.handleEvents()        
            
            time.sleep(0.1)


                        
    def stop(self):        
        
        print "IoTApp stopping"
        self.active = False
        print "IoTApp stopped"
        
        


iot_app = IoTApp()
iot_app.start()        