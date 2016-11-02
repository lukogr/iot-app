$(document).ready(function() {
    var networkFA = [];
    var optionsFA = [];
    var nodes = [];
    var edges = [];
    var nodesArray = [];
    var edgesArray = [];
    var iotStatusData;
    var oldUsers = [];
    var oldAllProbes = [];
    
    // Define colors
    var colors = {
      "network" : {
        true : "#57169a",
        false : "#808080"
      },
      "ts" : {
        true : "#f0a30a",
        false : "#808080"
      },
      "channel" : {
        true : "#aa00ff",
        false : "#808080"
      },
      "sensor" : {
        true : "#aa00ff",
        false : "#808080"
      },
         
    }
    
    var prepareIotDraw = function() {
      var users = Object.keys(iotStatusData['status']);
      var allProbes = [];
      var statusContainerHtml = "";
      var iotStatus = [];
      
      // Prepare array with probes identifiers
      for (var user in users) {
        var pro = Object.keys(iotStatusData['status'][users[user]]['iot']);
        for (var p in pro) {
          allProbes.push(pro[p]);
        }
      }
      
      // Compare if new user or probe appears
      var cmp1 = _.isEqual(users, oldUsers);
      var cmp2 = _.isEqual(allProbes, oldAllProbes);
      
      // Redraw vis map if new user or probe appears
      if (cmp1 == false || cmp2 == false) {
          oldUsers = users;
          oldAllProbes = allProbes;
        
          // prepare header and empty vis network elements for each user
          for (var user in users) {
            statusContainerHtml += "<div class='user-network'>";
            statusContainerHtml += "<h2><i class='fa fa-user'></i> User " + users[user] + "</h2>";
            statusContainerHtml += "<div id='network-" + users[user] + "' class='mynetwork'>Loading...</div>";
            statusContainerHtml += "</div>"
          }

          // insert empty vis elements into webpage
          $( "#status-container" ).html(statusContainerHtml);

          // second loop for draw initial network in vis elements
          for (var user in users) {
            user = users[user];
            
            var tsStatus = iotStatusData['status'][user]["account_created"];
            
            nodes[user] = new vis.DataSet();

            optionsFA[user] = {
              "physics": {
                "enabled": false
              },
              layout: {
                hierarchical: {
                  direction: 'LR'
                }
              },
              interaction:{
                dragNodes:false,
                dragView: false,
              },
              groups: {
                sensors: {
                  shape: 'icon',
                  icon: {
                    face: 'FontAwesome',
                    code: '\uf1eb',
                    size: 50,
                    color: colors["sensor"][true] // static color setting
                  }
                },          
                hierarchicalRepulsion: {
                  centralGravity: 0.0,
                  springLength: 100,
                  springConstant: 0.01,
                  nodeDistance: 120,
                  damping: 0.09
                },
              }
            };
            

            // create an array with nodes
            nodesArray[user] = [];
            edgesArray[user] = [];
            var probes = Object.keys(iotStatusData['status'][user]['iot']);
           
            // Add Network and ThingSpeak to vis map
            nodesArray[user].push(
              
              // id: 200 - ThingSpeak
              {
                id: 200,
                label: 'ThingSpeak',
                shape: 'icon',
                level: 2,
                icon: {
                  face: 'FontAwesome',
                  code: '\uf1c0',
                  size: 50,
                  color: colors["ts"][tsStatus]
                }
              }
            );

            for (var probe in probes) {
              var channelStatus = iotStatusData['status'][user]["iot"][probes[probe]]["channel_created"];
              var networkStatus = iotStatusData['status'][user]["iot"][probes[probe]]["path_established"];
              
              // Add probes to vis map
              nodesArray[user].push(
                {
                  id: parseInt(probe),
                  label: 'Probe '+probes[probe],
                  group: 'sensors',
                  level: 0
                }
              );
              
              // Add Channels to vis map
              nodesArray[user].push(
                {
                  id: parseInt(probes[probe])*2,
                  label: 'Channel '+probes[probe],
                  level: 3,
                  shape: 'icon',
                  icon: {
                    face: 'FontAwesome',
                    code: '\uf201',
                    size: 50,
                    color: colors["channel"][channelStatus]
                  }
                }
              );
              
              // Add Networks to vis map
              nodesArray[user].push(
                {
                  id: parseInt(probes[probe])*3,
                  label: 'Network',
                  level: 1,
                  shape: 'icon',
                  icon: {
                    face: 'FontAwesome',
                    code: '\uf0c2',
                    size: 50,
                    color: colors["network"][networkStatus]
                  }
                }
              );
              
              
              // Add connection Probes<->Network
              edgesArray[user].push({from: parseInt(probe), to: parseInt(probes[probe])*3});
              // Add connection ThingSpeak<->Probes
              edgesArray[user].push({from: parseInt(probes[probe])*2, to: 200});
              // Add connection Network<->ThingSpeak
              edgesArray[user].push({from: parseInt(probes[probe])*3, to: 200});
              
            }
            
            nodes[user] = new vis.DataSet(nodesArray[user]);

            edges[user] = new vis.DataSet(edgesArray[user]);

            // create a network
            var containerFA = document.getElementById("network-" + user);
            var dataFA = {
              nodes: nodes[user],
              edges: edges[user]
            };

            networkFA[user] = new vis.Network(containerFA, dataFA, optionsFA[user]);
          }
      } else {
        // Update elements states
        updateIotStatus();
      }
    };
    
    var updateIotStatus = function() {
      var users = Object.keys(iotStatusData['status']);
      
      // for each user update the elements states
      for (var user in users) {
        user = users[user];
        var probes = Object.keys(iotStatusData['status'][user]['iot']);
        var tsStatus = iotStatusData['status'][user]["account_created"];

        nodes[user].update([{id:200, icon: {"color" : colors["ts"][tsStatus]}}]);        

        for (var probe in probes) {
          var channelStatus = iotStatusData['status'][user]["iot"][probes[probe]]["channel_created"];
          var networkStatus = iotStatusData['status'][user]["iot"][probes[probe]]["path_established"];

          nodes[user].update(
            [
              {
                id:parseInt(probes[probe])*2, 
                icon: {
                  "color" : colors["channel"][channelStatus]
                }
              }
            ]
          );
          nodes[user].update(
            [
              {
                id:parseInt(probes[probe])*3, 
                icon: {
                  "color" : colors["network"][networkStatus]
                }
              }
            ]
          );
        }
      
      }
    };
    
    
    var updateAjaxIotStatus = function() {
      $.ajax({
        url: "http://10.0.0.54:5000/get_app_status",
        success: function( result ) {
          iotStatusData = result;
          prepareIotDraw();
        }
      });
    };
    
    // run map update in the loop
    var timer = setInterval(updateAjaxIotStatus, 1000);

  });