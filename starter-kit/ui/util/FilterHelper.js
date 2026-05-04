// ui/util/FilterHelper.js
// Encapsulates all filter/search logic for the backlog view.
//
// SRP: this module has one job — translate user input (search text + dropdowns)
//      into OData Filter objects. The Backlog controller delegates here; it does
//      not contain any filter-building logic itself.
//
// OCP: to add a new searchable field, add one entry to FIELD_FILTER_MAP.
//      The Backlog controller and _parseJQL method do not need to change.

sap.ui.define([
  "sap/ui/model/Filter",
  "sap/ui/model/FilterOperator"
], function (Filter, FilterOperator) {
  "use strict";

  // Maps JQL token field names to OData filter builders.
  // OCP: extend this map to support new query fields — do not edit _fieldFilter.
  var FIELD_FILTER_MAP = {
    status  : function (v) { return new Filter("status",      FilterOperator.EQ,       v); },
    priority: function (v) { return new Filter("priority",    FilterOperator.EQ,       v); },
    assignee: function (v) { return new Filter("assignee",    FilterOperator.Contains,  v); },
    sprint  : function (v) { return new Filter("sprint/name", FilterOperator.Contains,  v); },
    points  : function (v) { return new Filter("storyPoints", FilterOperator.EQ, parseInt(v, 10)); },
    sp      : function (v) { return new Filter("storyPoints", FilterOperator.EQ, parseInt(v, 10)); }
  };

  // Parses JQL-style tokens: status:New priority:High assignee:alice "free text"
  function _parseJQL(sQuery) {
    var aFilters = [];
    var re = /(\w+):"([^"]+)"|(\w+):(\S+)|"([^"]+)"|(\S+)/g;
    var m;
    var aFreeText = [];

    while ((m = re.exec(sQuery)) !== null) {
      var sField = (m[1] || m[3] || "").toLowerCase();
      var sValue = m[2] || m[4] || m[5] || m[6];

      if (sField && FIELD_FILTER_MAP[sField]) {
        aFilters.push(FIELD_FILTER_MAP[sField](sValue));
      } else if (!sField) {
        aFreeText.push(sValue);
      }
    }

    if (aFreeText.length) {
      var sFreeText = aFreeText.join(" ");
      aFilters.push(new Filter({
        filters: [
          new Filter("title",       FilterOperator.Contains, sFreeText),
          new Filter("description", FilterOperator.Contains, sFreeText)
        ],
        and: false
      }));
    }

    return aFilters;
  }

  return {
    // Combines JQL search bar with quick-filter dropdowns (AND logic).
    // Returns a single Filter or empty array (no filter) for OData binding.
    buildFilters: function (sQuery, sStatus, sPriority, sSprintId) {
      var aFilters = [];

      if (sQuery && sQuery.trim()) {
        aFilters = aFilters.concat(_parseJQL(sQuery.trim()));
      }
      if (sStatus)   { aFilters.push(new Filter("status",    FilterOperator.EQ, sStatus));   }
      if (sPriority) { aFilters.push(new Filter("priority",  FilterOperator.EQ, sPriority)); }
      if (sSprintId) { aFilters.push(new Filter("sprint_ID", FilterOperator.EQ, sSprintId)); }

      return aFilters.length ? new Filter({ filters: aFilters, and: true }) : [];
    }
  };
});
