$(function() {
    function OctoCamDoxSettingsViewModel(parameters) {
        var self = this;
        self.settings = parameters[0];

        // This will get called before the ViewModel gets bound to the DOM, but after its depedencies have
        // already been initialized. It is especially guaranteed that this method gets called _after_ the settings
        // have been retrieved from the OctoPrint backend and thus the SettingsViewModel been properly populated.
        self.onBeforeBinding = function() {
            self.settings = self.settings.settings;
        };

        // Execute certain actions when the radio buttons are pressed
        window.onload = function() {
          document.getElementById("option-normal").onclick = function fun() {
              self.resetOtherButtons("normalMode");
            };
          document.getElementById("option-force-LTR").onclick = function fun() {
              self.resetOtherButtons("forceLTR");
            };
          document.getElementById("option-force-RTL").onclick = function fun() {
              self.resetOtherButtons("forceRTL");
            };
          };

        // Reset the options for the non selected radio buttons
        self.resetOtherButtons = function(mode){
          if(mode == "normalMode"){
            self.settings.plugins.OctoCamDox.normalMode("on");
            self.settings.plugins.OctoCamDox.forceLTR("off");
            self.settings.plugins.OctoCamDox.forceRTL("off");
          }
          if(mode == "forceLTR"){
            self.settings.plugins.OctoCamDox.normalMode("off");
            self.settings.plugins.OctoCamDox.forceLTR("on");
            self.settings.plugins.OctoCamDox.forceRTL("off");
          }
          if(mode == "forceRTL"){
            self.settings.plugins.OctoCamDox.normalMode("off");
            self.settings.plugins.OctoCamDox.forceLTR("off");
            self.settings.plugins.OctoCamDox.forceRTL("on");
          }
        };

        self.getImageRes = function() {
            console.log("Updating Camera Resolution, make sure the printer is online!");
            $.ajax({
                url: "api" + PLUGIN_BASEURL + "OctoCamDox",
                type: "GET",
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                //data: JSON.stringify(data),
                success: function(response) {
                    if(response.hasOwnProperty("width")) {
                        self.settings.plugins.OctoCamDox.picture_width(response.width);
                    }
                    if(response.hasOwnProperty("height")) {
                        self.settings.plugins.OctoCamDox.picture_height(response.height);
                    }

                }
            });
        };
    }
    // This is how our plugin registers itself with the application, by adding some configuration information to
    // the global variable ADDITIONAL_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push({
        // This is the constructor to call for instantiating the plugin
        construct: OctoCamDoxSettingsViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request here is the order
        // in which the dependencies will be injected into your view model upon instantiation via the parameters
        // argument
        // dependencies: ["settingsViewModel", "controlViewModel", "connectionViewModel"],
        dependencies: ["settingsViewModel"],

        // Finally, this is the list of all elements we want this view model to be bound to.
        elements:["#settings_plugin_OctoCamDox"]
    });
});
