odoo.define('web_dynamic_dashboard.DDashboardView', function (require) {
"use strict";
/*---------------------------------------------------------
 * OpenERP web_dynamic_dashboard
 *---------------------------------------------------------*/

var core = require('web.core');
var data = require('web.data');
var AbstractView = require('web.AbstractView');
var BasicView = require('web.BasicView');
var view_registry = require('web.view_registry');
var _lt = core._lt;
var DDashboardModel = require('web_dynamic_dashboard.DDashboardModel');
var DDashboardController = require('web_dynamic_dashboard.DDashboardController');
var DDashboardRenderer = require('web_dynamic_dashboard.DDashboardRenderer');

var DDashboardView = BasicView.extend({
    template: "DDashboardView",
    display_name: _lt('DDashboard'),
    events: {
        // 'click .o_calendar_sidebar_toggler': 'toggle_full_width',
    },
    icon: 'fa-tachometer',
    template: "DDashboardView",
    config: {
        Model: DDashboardModel,
        Controller: DDashboardController,
        Renderer: DDashboardRenderer,
    },
    

    init: function () {
        this.view_type = 'ddashboard';
        console.log("Init", this);
        this._super.apply(this, arguments);
    }
});


    view_registry.add('ddashboard', DDashboardView);

    return DDashboardView;
});
