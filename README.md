# iot-app
**IoT/SDN application with cloud orchestrator module.**

IoT/SDN network application resolve problem of IoT traffic management in a Smart City divided into smart multi-tenant spaces.

The iot-app is sollution for the automated initiation and provisioning of end-to-end communication channels through the SDN-based metro network infrastructure from “internet things” to dedicated services deployed in the cloud via containers for data storage, visualization and analysis.

Recipients of the solution are administrators of inteligent spaces (Smart City, Smart Building) equipped with multiple IoT devices, who would like to optimize IoT traffic management by the orchestration of common network and containerized cloud resources.

The biggest advantages of IoT application:
- orchestration of shared network and containerized cloud resources from one common network application
- new IoT devices recognized automaticly by network application - just plug IoT gateway to SDN switch
- all owners of IoT devices can get easy access to IoT data through dedicated Thingspeak portal

This solution is prepared in close collaboration between research and commercial organizations: Poznan Supercomputing and Networking Center, NoviFlow and Spirent.

Two software modules are included in this repository:
  1. iot application 
  2. cloud orchestrator

Application uses some extensions of the OpenFlow 1.3 protocol implemented by NoviFlow like:
- matching to UDP payload: first 10 bytes of the text protocol sending inside UDP is ID of the sensor. Based on the ID application:
  - using cloud orchestrator:
    - automaticly create LXC container in the cloud 
    - run thingspeak service inside LXC container (service is dedicated for owner of the "thing") 
    - create IoT parser instance (parser gets data from UDP packet and uses thingspeak API to put these data into service)
  - set up path in SDN network using OpenFlow 1.3 protocol
- adding metadata to the UDP packet
  - extra 25 bytes are added to UDP with information useful for parser (sensor type, UDP port number and thingspeak API key)   

Cloud orchestrator should be run first before iot application. 

**To run cloud orchestrator:**
  1. Run python script
```
# iot_fwd.py
```
Iot_fwd provides Rest API for management of the container (lxc launch, exec, delete).
   
**To run iot_app:**
  1. Install required Python packages:
  ```
  $ apt-get install python-pip python-dev
  $ pip install ryu repoze.lru stevedore greenlet pyyaml scapy
  ```
  This code has been tested using Ryu version 3.26, more recent versions of Ryu may not work.

  2. Start Ryu with novi_rest_iot_app.py application
  ```
  $ ryu-manager novi_rest_iot_app.py
  ```

Live demonstration
===
This software modules allow to prepare live demonstration "IoT ecosystem over programmable SDN infrastructure for Smart City applications". 

Demonstration was first presented at the TNC16 conference in Prague (12-16.06.2016) together with NoviFlow and Spirent companies.

![alt tag](https://github.com/lukogr/iot-app/blob/master/arch/iot_app_demo_arch.png)

Current status of the network, cloud, containers and services can me monitored using web browser (Firefox is recommended).
  1. General information (json format)
    ```
    http://{iot_app_IPaddress}
    ```
  2. Data center monitoring tools:
    ```
    http://{iot_app_IPaddress}:5000/static/iot-dc/ui/index.html
    ```    
  3. Demonstration architecture:
    ```
    http://{iot_app_IPaddress}:5000/control_panel
    ```
