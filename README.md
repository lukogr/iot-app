# iot-app
**IoT application with cloud orchestrator module.**

Two software modules are included:
  1. iot application 
  2. cloud orchestrator

IoT application based on the configuration file can manage network and clould resources for dynamicly seting up channels from "things" to the cloud through the SDN infrastructure. 

Application uses some extensions of the OpenFlow 1.3 protocol implemented by NoviFlow like:
- matching to UDP payload: first 10 bytes of the text protocol sending inside UDP is ID of the sensor. Based on the ID application:
  - automaticly create LXC container in the cloud using cloud orchestrator
  - run thingspeak service inside LXC dedicated for owner of the "thing" using cloud orchestrator
  - create IoTparser instance using cloud orchestrator (parser analyse UDP packet and using thingspeak API put data into service)
  - setup path in SDN network using OpenFlow 1.3 protocol
- adding metadata to the UDP packet
  - 25 bytes are added to UDP with information useful for parser (sensor type and thingspeak API key)   

**To run cloud orchestrator:**
```
# iot_fwd.py
```
   
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

This software modules were used during demonstration "IoT ecosystem over programmable SDN infrastructure for Smart City applications" at the TNC16 conference in Prague (12-16.06.2016) prepared together with NoviFlow and Spirent companies.
