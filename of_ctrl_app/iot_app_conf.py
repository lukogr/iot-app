#IoT App configuration

demo_config = {
    "channels":{
        # libelium
        "403472527":{
            "type":"Ambient",
            "user":"libelium-user",
            "channel_created":False,
            "ak": None,
            "path_established":False
        },
        "403458164":{
            "type":"SmartCity",
            "user":"libelium-user",
            "channel_created":False,
            "ak": None,
            "path_established":False
        },
        # spirent
        "123456789":{
            "type":"SpirentChannel",
            "user":"spirent-user",
            "channel_created":False,
            "ak": None,
            "path_established":False
        },
        "987654321":{
            "type":"SpirentChannel",
            "user":"spirent-user",
            "channel_created":False,
            "ak": None,
            "path_established":False
        },        
        # generator
        "111222333":{
            "type":"TestChannel",
            "user":"generator-user",
            "channel_created":False,
            "ak": None,
            "path_established":False
        },
        "444555666":{
            "type":"TestChannel",
            "user":"generator-user",
            "channel_created":False,
            "ak": None,
            "path_established":False
        }      
    },
    "users":{
        "libelium-user":
        {
            "service_IP":"10.0.0.70",
            "service_port":3000,
            "iot_server_IP":"192.168.21.4",
            "iot_server_port":5555,
            "src_ip":"192.168.21.1", 
            "mail":"lukaszog@man.poznan.pl",
            "password":"12345678",
            "time_zone":"Warsaw",
            "account_created":False,
            "APIkey":None,
            "ID":None,
            "map":"map1",
            "udp_socket_created":False,
            "lxc_created":False
        },       
        
        "generator-user":
        {
            "service_IP":"10.0.0.70",
            "service_port":3001,
            "iot_server_IP":"192.168.21.4",
            "iot_server_port":8888,
            "src_ip":"192.168.21.1", 
            "mail":"lukaszog@man.poznan.pl",
            "password":"test1234",
            "time_zone":"Warsaw",
            "account_created":False,
            "APIkey":None,
            "ID":None,
            "map":"map2",
            "udp_socket_created":False,
            "lxc_created":False
        },

        "spirent-user":
        {
            "service_IP":"10.0.0.70",
            "service_port":3002,
            "iot_server_IP":"192.168.22.4",
            "iot_server_port":7777,
            "src_ip":"192.168.22.1", 
            "mail":"lukaszog@man.poznan.pl",
            "password":"test1234",
            "time_zone":"Warsaw",
            "account_created":False,
            "APIkey":None,
            "ID":None,
            "map":"map3",
            "udp_socket_created":False,
            "lxc_created":False
        }        
    },
    "network_maps":{
        "map1":{
            147058196517: {
                "flows": [
                    {"in_port": 14,"out_port": 8}
                ],
                "installed": False
            }
        },
        "map2":{
            147058196517: {
                "flows": [
                    {"in_port": 18,"out_port": 8}
                ],
                "installed": False
            },            
            147058196529:{
                "flows": [
                    {"in_port": 24 ,"out_port": 20}
                ],
                "installed": False
            }
        },
        "map3":{
            147058196517: {
                "flows": [
                    #{"in_port": 24,"out_port": 26}#back to Spirent
                    {"in_port": 24,"out_port": 16}
                ],
                "installed": False
            },
            147058196523: {
                "flows": [
                    {"in_port": 20,"out_port": 6}
                ],
                "installed": False
            }              
        }
    },
    "NoviSwitches": {
        147058196523: "NoviSwitch#1",
        147058196529: "NoviSwitch#2",
        147058196517: "NoviSwitch#4"
    }
}
channel_type_short = {
    "SmartCity":"SC",
    "Ambient":"AC",
    "TestChannel":"TC",
    "SpirentChannel":"SP"
}
iot_fwd_port = 5001