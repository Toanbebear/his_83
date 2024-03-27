odoo.define('web_dynamic_dashboard.DDashboardController', function (require) {
"use strict";

/**
 * Calendar Controller
 *
 * This is the controller in the Model-Renderer-Controller architecture of the
 * calendar view.  Its role is to coordinate the data from the calendar model
 * with the renderer, and with the outside world (such as a search view input)
 */

var AbstractController = require('web.AbstractController');
var dialogs = require('web.view_dialogs');
var Dialog = require('web.Dialog');
var core = require('web.core');

var _t = core._t;
var QWeb = core.qweb;

var DDashboardController = AbstractController.extend({
    init: function (parent, model, renderer, params) {
        params.viewType = "ddashboard";
        this._super.apply(this, arguments);
    }
});

return DDashboardController;

});
