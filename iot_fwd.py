# Copyright (C) 2016 PSNC
# Lukasz Ogrodowczyk (PSNC) <lukaszog_at_man.poznan.pl>
#
# IoT cloud orchestrator module


import subprocess, socket, requests, json, threading, time, requests, logging
from cherrypy import wsgiserver
from flask import Flask, jsonify


app = Flask(__name__)


sockets = []
service_IP = "10.0.0.70"

#---------------------------------------------------------#
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
        self.server.stop()
        print "Flask stopped"

#---------------------------------------------------------#
class UDPsocket(threading.Thread):
    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        self.active = False
        self.ip = ip
        self.port = port
        self.sock = None

    def parseData(self, data):

        list_data = {}
        parsed_data = {}
        list_data = data.split("#",4)
        parsed_data["type"] = list_data[1]
        parsed_data["ak"] = list_data[2]
        parsed_data["service_port"] = int(list_data[3])
        list_data = list_data[4]
        list_data = list_data.split("#")
        parsed_data["ID"] = list_data[0]


        if parsed_data["type"] == "SC":
            parsed_data["name"] = list_data[3]
            parsed_data["bat"] = list_data[5].split(":")[1]
            parsed_data["temperature"] = list_data[7].split(":")[1]
            parsed_data["noise"] = list_data[8].split(":")[1]
            parsed_data["ultrasound"] = list_data[9].split(":")[1]
            parsed_data["luminocity"] = list_data[10].split(":")[1]
       
            payload = {
                "api_key":parsed_data["ak"],
                "field1":parsed_data["bat"],
                "field2":parsed_data["temperature"],
                "field3":parsed_data["noise"],
                "field4":parsed_data["ultrasound"],
                "field5":parsed_data["luminocity"],
            }
            #update thingspeak channel: 
            self.updateChannel(payload, service_IP, parsed_data["service_port"])

        if parsed_data["type"] =="AC":

            if list_data[5].split(":")[0] == 'HUMB':
                parsed_data["name"] = list_data[3]
                parsed_data["humidity"] = list_data[5].split(":")[1]
                parsed_data["luminocity"] = list_data[6].split(":")[1]
                parsed_data["lux"] = list_data[7].split(":")[1]

                payload = {
                    "api_key":parsed_data["ak"],
                    "field2":parsed_data["humidity"],
                    "field3":parsed_data["luminocity"],
                    "field4":parsed_data["lux"]
                }
                
                #update thingspeak channel          
                self.updateChannel(payload, service_IP, parsed_data["service_port"])


            else:
                parsed_data["name"] = list_data[3]
                parsed_data["bat"] = list_data[5].split(":")[1]
                
                payload = {
                    "api_key":parsed_data["ak"],
                    "field1":parsed_data["bat"],
                }
               
                #update thingspeak channel          
                self.updateChannel(payload, service_IP, parsed_data["service_port"])             
        
        if parsed_data["type"] == "TC":
            parsed_data["random"] = list_data[1].split(":")[1]
  
            payload = {
                "api_key":parsed_data["ak"],
                "field1":parsed_data["random"]
            }
            #update thingspeak channel: 
            self.updateChannel(payload, service_IP, parsed_data["service_port"])

        if parsed_data["type"] == "SP":
            parsed_data["random"] = list_data[1].split(":")[1]
  
            payload = {
                "api_key":parsed_data["ak"],
                "field1":parsed_data["random"]
            }
            #update thingspeak channel: 
            self.updateChannel(payload, service_IP, parsed_data["service_port"])


    def updateChannel(self, payload, service_IP, service_port):
        print "Updating thingspeak channel (IP: %s, port:%s)..."%(service_IP, service_port)
        header = {'content-type': 'application/json'}
        try:        
            response = requests.post("http://"+service_IP+":"+str(service_port)+"/update", headers=header, 
                            data=json.dumps(payload))  
            print "Updating channel response: %s"%(response.json())
        except:
            print "ERROR: some problem during channel updating (IP: %s, port:%s)!"%(service_IP, service_port)

    def run(self):
        # run flask service:
        print "Starting udp socket (ip: %s, port: %s)..."%(self.ip, self.port)   
        
        self.sock = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP

        try:
            self.sock.bind((self.ip, int(self.port)))
            print "UDP socket started."
            self.active = True
        except:
            print "ERROR during socket binding!"
            self.stop()

        while self.active:  

            data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
            print "data from %s: %s"%(addr, data)

            self.parseData(data)

             
    def stop(self):                
        if self.active:
            print "UDP socket stopping (ip: %s , port: %s)..."%(self.ip, self.port)        
            self.sock.close()
            self.active = False      
            print "UDP socket stopped"
        print "UDP socket end."

#---------------------------------------------------------#

def createUDPsocket(ip, port):

    udp_socket = UDPsocket(ip,port)
    udp_socket.start()

    time.sleep(0.1) #wait to check if success
    if udp_socket.isAlive():
        sockets.append(udp_socket)
        return True
    else:
        return False


@app.route("/test")
def test():     
    return jsonify(status="ok") 

@app.route("/create_udp_socket/<socket>")
def create_UDP_socket(socket):
    print "Creating UDP socket: %s"%(socket)
    data = socket.split("&")
    ip = data[0].split("\"")[1]     
    port = data[1].split("\"")[0]
    if createUDPsocket(ip,port):
        return jsonify(status="ok") 
    else:
        return jsonify(status="error") 

@app.route("/port_redirect/<redir>")
def port_redirect(redir):
    print "Redirection: %s"%(redir)
    data = redir.split("&")
    ip_s = data[0].split("\"")[1]     
    port_s = data[1]
    ip_d = data[2]
    port_d = data[3].split("\"")[0]

    command = ["redir", "--laddr="+ip_s, "--lport="+port_s, "--caddr="+ip_d, "--cport="+port_d]
    subprocess.Popen(command)    
    return jsonify(status="ok")
    
@app.route("/lxc_script/<thingspeak_name>")    
def lxc_script(thingspeak_name):
    print "thingspeak %s running..."%(thingspeak_name)
    command_run_script = ["lxc", "exec", thingspeak_name, "--", "/bin/bash", "/home/ubuntu/run.sh"]
    proc = subprocess.Popen(command_run_script, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = proc.communicate()
    if stderr_data == "":
        return jsonify(status="ok")
    else:
        return jsonify(status=stderr_data)

@app.route("/lxc_run/<thingspeak_name>")
def lxc_run(thingspeak_name):
    print "LXC %s starting..."%(thingspeak_name)
    lxc_run_command = ["lxc", "launch", "thingspeak", thingspeak_name]
    proc = subprocess.Popen(lxc_run_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = proc.communicate()
    if stderr_data == "":
        return jsonify(status="ok")
    else:
        return jsonify(status=stderr_data)

@app.route("/lxc_del/<thingspeak_name>")
def lxc_del(thingspeak_name):
    print "LXC %s deleting..."%(thingspeak_name)
    lxc_run_command = ["lxc", "stop", thingspeak_name]
    proc = subprocess.Popen(lxc_run_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = proc.communicate()
    if stderr_data == "":
        lxc_run_command = ["lxc", "delete", thingspeak_name]
        proc = subprocess.Popen(lxc_run_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_data, stderr_data = proc.communicate()
        if stderr_data == "":
            return jsonify(status="ok")
        else:
            return jsonify(status=stderr_data)
    else:
        return jsonify(status=stderr_data)

@app.route("/lxc_list/<thingspeak>")
def lxc_list(thingspeak):
    print "LXC %s get status..."%(thingspeak)
    lxc_list_command = ["lxc", "list", thingspeak, "--format", "json"]
    proc = subprocess.Popen(lxc_list_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = proc.communicate()
    if stderr_data == "":
        res_j = json.loads(stdout_data, encoding="utf-8")
        if res_j != []:
            for item in res_j[0]["state"]["network"]['eth0']["addresses"]:
                if item["family"] =="inet":
                    ip = item["address"]
                    return jsonify(status=res_j[0]["status"], ip=ip) 
        return jsonify(status="error")
    else:
        return jsonify(status=stderr_data)


if __name__ == "__main__":
    
    flask_app = FlaskAPP()
    flask_app.start()


    #may break by ctrl+c    
    try:
                    
        # Wait forever, so we can receive KeyboardInterrupt.
        while True:
            time.sleep(1)
                 
    except (KeyboardInterrupt, SystemExit):
        print "FELIX : ^C received"
        
        if flask_app.isAlive():
            flask_app.stop()  
        
        for s in sockets:
            if s.isAlive():
                s.stop()  

        import os, signal
        os._exit(1)        
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)
       
    # We never get here.
    raise RuntimeError, "not reached"
#---------------------------------------------------------#      