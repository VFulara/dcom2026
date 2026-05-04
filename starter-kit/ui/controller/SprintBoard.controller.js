sap.ui.define([
  "sap/ui/core/mvc/Controller",
  "sap/m/IconTabFilter",
  "sap/m/List",
  "sap/m/ObjectListItem",
  "sap/m/ObjectAttribute",
  "sap/m/ObjectStatus",
  "sap/m/MessageBox",
  "sap/m/MessageToast",
  "sap/ui/model/Filter",
  "sap/ui/model/FilterOperator",
  "../util/Formatters"
], function (Controller, IconTabFilter, List, ObjectListItem, ObjectAttribute, ObjectStatus,
             MessageBox, MessageToast, Filter, FilterOperator, Formatters) {
  "use strict";

  return Controller.extend("planning.board.controller.SprintBoard", {

    formatter: Formatters,

    onInit: function () {
      var oRouter = this.getOwnerComponent().getRouter();
      oRouter.getRoute("sprintBoard").attachPatternMatched(this._loadSprints, this);
    },

    _loadSprints: function () {
      // DIP: consume SprintService (sprint bounded context), not the default BacklogService model.
      var oSprintModel = this.getOwnerComponent().getModel("sprint");
      var oTabBar = this.byId("sprintTabBar");
      oTabBar.destroyItems();

      oSprintModel.bindList("/Sprints", null, null, [
        new Filter("status", FilterOperator.NE, "Completed")
      ]).requestContexts(0, 20).then(function (aContexts) {
        aContexts.forEach(function (oCtx) {
          oTabBar.addItem(this._buildSprintTab(oCtx.getObject()));
        }.bind(this));
      }.bind(this));
    },

    // IconTabBar does not support OData-bound tab generation with nested story lists
    // in OpenUI5 1.120 — programmatic construction is the necessary approach here.
    // SRP: this method builds ONE tab for ONE sprint. All strings use i18n keys.
    _buildSprintTab: function (oSprint) {
      var sLabel = oSprint.name + (oSprint.status ? " [" + oSprint.status + "]" : "");

      // Stories are read from SprintService — the sprint board displays stories
      // in sprint context. Mutations go through BacklogService (DDD bounded contexts).
      var oList = new List({ noDataText: this._t("noStoriesInSprint") });
      oList.setModel(this.getOwnerComponent().getModel("sprint"));
      oList.bindItems({
        path    : "/Stories",
        filters : [new Filter("sprint_ID", FilterOperator.EQ, oSprint.ID)],
        template: new ObjectListItem({
          title      : "{title}",
          number     : "{storyPoints}",
          numberUnit : "pts",
          firstStatus: new ObjectStatus({
            text : "{status}",
            state: "{path: 'status', formatter: '.formatter.statusToState'}"
          }),
          attributes: [
            new ObjectAttribute({ text: "{priority}" }),
            new ObjectAttribute({ text: "{assignee}" })
          ]
        })
      });

      return new IconTabFilter({ text: sLabel, key: oSprint.ID, content: [oList] });
    },

    // ── Sprint Creation ───────────────────────────────────────────────────

    onNewSprint: function () {
      this.byId("newSprintDialog").open();
    },

    onCreateSprint: function () {
      var sName = this.byId("sprintName").getValue().trim();
      if (!sName) {
        MessageBox.error(this._t("errorSprintNameRequired"));
        return;
      }
      var sStartDate = this.byId("sprintStartDate").getValue() || undefined;
      var sEndDate   = this.byId("sprintEndDate").getValue()   || undefined;

      var oContext = this.getOwnerComponent().getModel("sprint")
        .bindList("/Sprints")
        .create({ name: sName, startDate: sStartDate, endDate: sEndDate, status: "Planned" });

      oContext.created().then(function () {
        MessageToast.show(this._t("sprintCreated"));
        this.byId("newSprintDialog").close();
        this._resetSprintDialog();
        this._loadSprints();
      }.bind(this)).catch(function (oErr) {
        MessageBox.error(this._t("errorCreateFailed") + ": " + (oErr.message || oErr));
      }.bind(this));
    },

    onCancelSprintDialog: function () {
      this.byId("newSprintDialog").close();
      this._resetSprintDialog();
    },

    _resetSprintDialog: function () {
      this.byId("sprintName").setValue("");
      this.byId("sprintStartDate").setValue("");
      this.byId("sprintEndDate").setValue("");
    },

    // ── Navigation ────────────────────────────────────────────────────────

    onNavToBacklog: function () {
      this.getOwnerComponent().getRouter().navTo("backlog");
    },

    // ── Helpers ───────────────────────────────────────────────────────────

    _t: function (sKey) {
      return this.getView().getModel("i18n").getResourceBundle().getText(sKey);
    }
  });
});
