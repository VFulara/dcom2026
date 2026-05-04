sap.ui.define([
  "sap/ui/core/mvc/Controller",
  "sap/m/MessageBox",
  "sap/m/MessageToast",
  "sap/ui/model/json/JSONModel",
  "../util/Formatters",
  "../util/FilterHelper"
], function (Controller, MessageBox, MessageToast, JSONModel, Formatters, FilterHelper) {
  "use strict";

  return Controller.extend("planning.board.controller.Backlog", {

    // Exposed on `this` so views can bind: formatter: '.formatter.priorityToState'
    // DIP: view depends on this abstraction, not on inline ternary logic.
    formatter: Formatters,

    onInit: function () {
      var oSprintsModel = new JSONModel({ rowSprints: [], filterSprints: [] });
      this.getView().setModel(oSprintsModel, "sprints");
      this._loadSprints();
    },

    // ── Sprint Reference Data ─────────────────────────────────────────────

    _loadSprints: function () {
      var oModel = this.getOwnerComponent().getModel();
      oModel.bindList("/Sprints").requestContexts(0, 100).then(function (aCtx) {
        var aSprints = aCtx.map(function (c) { return c.getObject(); });
        var oSprintsModel = this.getView().getModel("sprints");
        oSprintsModel.setProperty("/rowSprints",
          [{ key: "", name: this._t("noSprint") }].concat(
            aSprints.map(function (s) { return { key: s.ID, name: s.name }; })
          )
        );
        oSprintsModel.setProperty("/filterSprints",
          [{ key: "", name: this._t("allSprints") }].concat(
            aSprints.map(function (s) { return { key: s.ID, name: s.name }; })
          )
        );
      }.bind(this));
    },

    // ── Search & Filter ───────────────────────────────────────────────────
    // SRP: filter logic is delegated to FilterHelper — this controller only
    //      reads the current UI state and hands it off.

    onSearch: function () {
      this._applyFilters();
    },

    onFilter: function () {
      this._applyFilters();
    },

    onClearFilters: function () {
      this.byId("searchField").setValue("");
      this.byId("filterStatus").setSelectedKey("");
      this.byId("filterPriority").setSelectedKey("");
      this.byId("filterSprint").setSelectedKey("");
      this._applyFilters();
    },

    _applyFilters: function () {
      var oCombined = FilterHelper.buildFilters(
        this.byId("searchField").getValue(),
        this.byId("filterStatus").getSelectedKey(),
        this.byId("filterPriority").getSelectedKey(),
        this.byId("filterSprint").getSelectedKey()
      );
      this.byId("storiesTable").getBinding("items").filter(oCombined);
    },

    // ── Story CRUD ────────────────────────────────────────────────────────

    onAddStory: function () {
      this._loadSprints();
      this.byId("addStoryDialog").open();
    },

    onCancelDialog: function () {
      this.byId("addStoryDialog").close();
      this._resetDialog();
    },

    onCreateStory: function () {
      var sTitle = this.byId("storyTitle").getValue().trim();
      if (!sTitle) {
        MessageBox.error(this._t("errorTitleRequired"));
        return;
      }
      var sPriority  = this.byId("storyPriority").getSelectedKey() || "Medium";
      var iPoints    = parseInt(this.byId("storyPoints").getValue(), 10) || 0;
      var sSprintKey = this.byId("storySprint").getSelectedKey();

      var oPayload = { title: sTitle, priority: sPriority, storyPoints: iPoints, status: "New" };
      if (sSprintKey) { oPayload.sprint_ID = sSprintKey; }

      var oContext = this.getOwnerComponent().getModel()
        .bindList("/Stories")
        .create(oPayload);

      // Wait for server confirmation before showing success — avoids false positives.
      oContext.created().then(function () {
        MessageToast.show(this._t("storyCreated"));
      }.bind(this)).catch(function (oErr) {
        MessageBox.error(this._t("errorCreateFailed") + ": " + (oErr.message || oErr));
      }.bind(this));

      this.byId("addStoryDialog").close();
      this._resetDialog();
    },

    // ── Inline Row Edits ──────────────────────────────────────────────────
    // DDD: story state transitions go through the OData service boundary,
    //      which enforces domain invariants (e.g. no negative points, valid sprint).

    onStatusChange: function (oEvent) {
      var oContext   = oEvent.getSource().getBindingContext();
      var sNewStatus = oEvent.getParameter("selectedItem").getKey();
      oContext.setProperty("status", sNewStatus);
    },

    onSprintChange: function (oEvent) {
      var oContext      = oEvent.getSource().getBindingContext();
      var sNewSprintKey = oEvent.getParameter("selectedItem").getKey();
      oContext.setProperty("sprint_ID", sNewSprintKey || null);
    },

    // ── Navigation ────────────────────────────────────────────────────────

    onNavToSprints: function () {
      this.getOwnerComponent().getRouter().navTo("sprintBoard");
    },

    onNavToReleases: function () {
      this.getOwnerComponent().getRouter().navTo("releases");
    },

    // ── Helpers ───────────────────────────────────────────────────────────

    _resetDialog: function () {
      this.byId("storyTitle").setValue("");
      this.byId("storyPriority").setSelectedKey("Medium");
      this.byId("storyPoints").setValue("");
      this.byId("storySprint").setSelectedKey("");
    },

    _t: function (sKey) {
      return this.getView().getModel("i18n").getResourceBundle().getText(sKey);
    }
  });
});
