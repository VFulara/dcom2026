// ui/util/Formatters.js
// Shared formatter module — imported by ALL controllers that display Stories or Sprints.
//
// DRY: priority→state and status→state mappings live here and NOWHERE else.
// DIP: views and controllers depend on this abstraction, not on inline ternary chains.
//
// To use in a controller:
//   sap.ui.define(["../util/Formatters", ...], function (Formatters, ...) {
//     onInit: function () { this.formatter = Formatters; }
//   });
// To use in a view binding:
//   state="{path: 'priority', formatter: '.formatter.priorityToState'}"

sap.ui.define([], function () {
  "use strict";

  // Maps are defined once — adding Critical, High, etc. means editing only this file.
  var _priorityStateMap = {
    Critical : "Error",
    High     : "Warning",
    Medium   : "Information",
    Low      : "Success"
  };

  var _statusStateMap = {
    Completed    : "Success",
    Blocked      : "Error",
    "In Progress": "Warning",
    "In Review"  : "Information",
    New          : "None"
  };

  return {
    priorityToState: function (sPriority) {
      return _priorityStateMap[sPriority] || "None";
    },

    statusToState: function (sStatus) {
      return _statusStateMap[sStatus] || "None";
    }
  };
});
