$(function() {
    function OctoCamDoxViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];
        self.control = parameters[1];
        self.connection = parameters[2];

        var _cameraGrid = {};
        var _cameraGridCanvas = document.getElementById('camGridCanvas');

        self.stateString = ko.observable("No file loaded");
        self.currentOperation = ko.observable("");
        self.debugvar = ko.observable("");

        self.layerSelectionEnabled = ko.observable(false);
        self.layerUpEnabled = ko.observable(false);
        //white placeholder images
        document.getElementById('headCameraImage').setAttribute( 'src', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3wMRCQAfAmB4CgAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAAAMSURBVAjXY/j//z8ABf4C/tzMWecAAAAASUVORK5CYII=');


        // This will get called before the ViewModel gets bound to the DOM, but after its depedencies have
        // already been initialized. It is especially guaranteed that this method gets called _after_ the settings
        // have been retrieved from the OctoPrint backend and thus the SettingsViewModel been properly populated.
        self.onBeforeBinding = function() {
            self.traySettings = self.settings.settings.plugins.OctoCamDox.tray;
            _cameraGrid = new camGrid(self.traySettings.columns(), self.traySettings.rows(), self.traySettings.boxsize(), _cameraGridCanvas);
            _cameraGridCanvas.addEventListener("click", self.onSmdTrayClick, false); //"click, dblclick"
            _cameraGridCanvas.addEventListener("dblclick", self.onSmdTrayDblclick, false); //"click, dblclick"
        };

        self.incrementLayer = function() {
            var value = self.layerSlider.slider('getValue') + 1;
            self.shiftLayer(value);
        };

        self.decrementLayer = function() {
            var value = self.layerSlider.slider('getValue') - 1;
            self.shiftLayer(value);
        };

        // catch mouseclicks at the tray for interactive part handling
        self.onSmdTrayClick = function(event) {
            var rect = _cameraGridCanvas.getBoundingClientRect();
            var x = Math.floor(event.clientX - rect.left);
            var y = Math.floor(event.clientY - rect.top);
            return _cameraGrid.selectPart(x, y);
        };

        self.onSmdTrayDblclick = function(event) {
            // highlight part on tray and find partId
            var partId = self.onSmdTrayClick(event);

            // execute pick&place operation
            if(partId) {
                // printer connected and not printing?
                if(self.connection.isOperational() || self.connection.isReady()) {
                    self.control.sendCustomCommand({ command: "M361 P" + partId});
                }
            }
        };



       self.onDataUpdaterPluginMessage = function(plugin, data) {
          if(plugin == "OctoCamDox") {
              if(data.event == "FILE") {
                  if(data.data.hasOwnProperty("cameraCoordinates")) {
                      self.stateString("Loaded file with GCodes");
                      //initialize the tray
                      _cameraGrid.erase();

					            //extract part information
                      if( data.data.hasOwnProperty("parts") ) {
          							var parts = data.data.parts;
          							for(var i=0; i < parts.length; i++) {
          								_cameraGrid.addPart(parts[i]);
          							}
          						}
                      }else{
                          self.stateString("No SMD part in this file!");
                            }
                      }
                  else if(data.event == "OPERATION") {
                      self.currentOperation(data.data.type + " part nr " + data.data.part);
                  }
                  else if(data.event == "ERROR") {
                      self.stateString("ERROR: \"" + data.data.type + "\"");
                      if(data.data.hasOwnProperty("part")) {
                          self.stateString(self.StateString + "appeared while processing part nr " + data.data.part);
                      }
                  }
                  else if(data.event == "INFO") {
                      self.stateString("INFO: \"" + data.data.type + "\"");
                  }
                  else if(data.event == "HEADIMAGE") {
                      document.getElementById('headCameraImage').setAttribute( 'src', data.data.src );
                  }
                  else if(data.event == "BEDIMAGE") {
                      document.getElementById('bedCameraImage').setAttribute( 'src', data.data.src );
                  }
              //self.debugvar("Plugin = OctoCamDox");
          }
      };
    }

    // This is how our plugin registers itself with the application, by adding some configuration information to
    // the global variable ADDITIONAL_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push({
        // This is the constructor to call for instantiating the plugin
        construct: OctoCamDoxViewModel,
        // This is a list of dependencies to inject into the plugin, the order which you request here is the order
        // in which the dependencies will be injected into your view model upon instantiation via the parameters
        // argument
        dependencies: ["settingsViewModel", "controlViewModel", "connectionViewModel"],
        // Finally, this is the list of all elements we want this view model to be bound to.
        elements: ["#tab_plugin_OctoCamDox"]
    });
});
