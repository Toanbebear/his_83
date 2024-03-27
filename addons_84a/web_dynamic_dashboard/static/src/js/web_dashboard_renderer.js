odoo.define('web_dynamic_dashboard.DDashboardRenderer', function (require) {
"use strict";

var AbstractRenderer = require('web.AbstractRenderer');
var Widget = require('web.Widget');
var core = require('web.core');
var TIMEOUT = 1000;
var CHARTCONTENTDOM = " .block_chart_content";
var CHARTTITLEDOM = " input.block_text";
var TILEVALUEDOM = " .block_tile_value";
var TILEH1DOM = " .block_tile_content h1"
var TILEUOMDOM = " .block_tile_uom";
var TILEDESCDOM = " input.block_text";
var TILEICONDOM = " .block_tile_header i";

var _t = core._t;

return AbstractRenderer.extend({
    template: "DDashboardView",
    events: _.extend({}, AbstractRenderer.prototype.events, {

    }),
    /**
     * @constructor
     * @param {Widget} parent
     * @param {Object} state
     * @param {Object} params
     */
    init: function (parent, state, params) {
        var self = this;
        console.log("Init", this, parent, state, params);
        self.parent_actions = parent.actions
        this._super.apply(this, arguments);
    },
    start: function () {
        var self = this;
        for (var key in self.parent_actions) {
            if (self.parent_actions.hasOwnProperty(key)) {      
                self.dashboard_id = self.parent_actions[key].context.dashboard_id;
            }
        }
        var dashboard_id = self.dashboard_id;
        console.log("Start", dashboard_id);
        setTimeout(function(){ 
            var link_dom_id = {};
            var last_block_size = 'init';
            var dashboard_by_id = {};
            var reset_block_data_by_id = {};
            var block_data_by_id = {};
            var block_elm_by_id = {};
            var is_manager = false;
            $.get("api/dashboard-name/"+dashboard_id, function(data, status){
                console.log("Data: ", data, "\nStatus: ", status);
                is_manager = data['is_manager']
                data = data['dashboards']
                for (var i=0; i < data.length; i++) {
                    var db = data[i];
                    $('#dashboard_selection').append('<option value="'+db['id']+'">'+db['name']+'</option>');
                    dashboard_by_id[db['id']] = db;
                }
                $('.block_config').show();
                if (is_manager) {
                    $('.sci_dashboard_mainbar .sci_add_block').show();
                    $('.block_config .config_toggle').show();
                    $('.block_config .config_detail').show();
                }else{
                    $('.block_config .config_toggle').hide();
                    $('.block_config .config_detail').hide();
                }
            });
            var draw_action_button = function(elmId, block_data) {
                if (block_data['action_dashboard_name']) {
                    $(elmId + ' .block_float_button').show();
                    $(elmId + ' .block_float_button span').text(block_data['action_dashboard_name']);
                } else if (block_data['menu_name']) {
                    $(elmId + ' .block_float_button').show();
                    $(elmId + ' .block_float_button span').text(block_data['menu_name'] + ' Menu');
                } else if (block_data['link']) {
                    $(elmId + ' .block_float_button').show();
                    $(elmId + ' .block_float_button span').text('Open URL');
                }
            }
            var draw_chart = function(block_type, elmId, block_data) {
                if (!($(elmId).length && $(elmId).is(":visible")))
                    return false
                if (block_type == 'tile') 
                    self.setTile(self, elmId, block_data);
                else if (block_type == 'area') 
                    return self.chartArea(self, elmId, block_data);
                else if (block_type == 'bar')  
                    return self.chartBar(self, elmId, block_data);
                else if (block_type == 'line-treshold')   
                    return self.chartLineTreshold(self, elmId, block_data);
                else if (block_type == 'hbar')     
                    return self.chartHBar(self, elmId, block_data);
                else if (block_type == 'line')   
                    return self.chartLine(self, elmId, block_data); 
                else if (block_type == 'donut')    
                    return self.chartDonut(self, elmId, block_data);
                else if (block_type == 'pie')    
                    return self.chartPie(self, elmId, block_data);
                else if (block_type == 'stackbar')  
                    return self.chartStackBar(self, elmId, block_data);
                return false;
            }
            var redraw_chart = function(block_id, save=false, reset_model=false){
                if (save) block_data_by_id[block_id]['save'] = save;
                if (reset_model) block_data_by_id[block_id]['reset_model'] = reset_model;
                var iteration_value = dashboard_by_id[dashboard_id]['iteration_value'];
                var block_url = iteration_value ? block_id + "/" + iteration_value : block_id;
                $.ajax("api/dashboard/block/" + block_url, {
                    data : JSON.stringify(block_data_by_id[block_id]),
                    contentType : 'application/json',
                    type : 'POST',
                    success: function(data, status){
                        console.log("Redraw Block Data: ", data, "\nStatus: ", status);
                        var block = data;
                        var elmId = '#block_'+block_id;

                        // Error
                        $(elmId + " .block_error").hide()
                        if ('error' in data) {
                            $(elmId + " .block_error").show().text(data['error'])
                        }

                        // Config
                        init_date_configuration(block);
                        if (reset_model) {
                            if (block['block_type'] != 'tile') {
                                block_data_by_id[block_id] = block;
                                $(elmId + " .block_config").remove()
                                var config_content = $('#block_chart_template .block_config').clone()
                                config_content.insertAfter($(elmId + " .block_chart_header"))
                                render_configuration(elmId);
                                init_configuration(block);
                                open_config(elmId);
                            } else {
                                block_data_by_id[block_id] = block;
                                $(elmId + " .block_config").remove()
                                var config_content = $('#block_tile_template .block_config').clone()
                                config_content.insertAfter($(elmId + " .block_error"))
                                render_configuration(elmId);
                                init_configuration(block);
                                open_config(elmId);
                            }
                        }

                        // Chart
                        $(elmId + " .block_chart_content").empty()
                        block_elm_by_id[block_id] = draw_chart(block['block_type'], elmId, block);
                        draw_action_button(elmId, block);
                    }
                })
            }
            var render_configuration = function(elmId="") {
                // Model, model_id
                $(elmId+" .block_config_model_id").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Model / Table',
                    ajax: {
                        url: "api/list/ir.model",dataType: "json", type: "GET",
                        data: function (params) { 
                            return {
                                "order": "name asc",
                                "domains": "['|', ('model', 'ilike', '" + params + "'), ('name', 'ilike', '" + params + "')]"
                            }
                        },
                        results: function (data) { return { results: $.map(data, function (item) { return {
                            text: item.name, slug: item.name, id: item.id
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['model_name'] ? {
                            'id': block_data_by_id[block_id]['model_name'],
                            'text': block_data_by_id[block_id]['model_name']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['model_id'] =  parseInt($(e.currentTarget).val())
                    redraw_chart(block_id, false, true);
                })
                
                // Measure, field_id
                $(elmId+" .block_config_field_id").select2({
                    tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Measure Field',
                    ajax: {
                        url: "api/list/ir.model.fields", dataType: "json", type: "GET",
                        data: function (params) {
                            var block_id = $( this ).parents('.dashboard_block').first().data("id");
                            var model_id = block_data_by_id[block_id]['model_id'];
                            return {
                                "domains": "[('ttype', 'in', ['float','integer','monetary']), ('store', '=', True), ('model_id', '=', " + model_id + " ), '|', ('name', 'ilike', '" + params + "'), ('field_description', 'ilike', '" + params + "')]",
                                "fields": "['id', 'field_description']"
                            };
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.field_description, slug: item.field_description, id: item.id
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['field_name'] ? {
                            'id': block_data_by_id[block_id]['field_name'],
                            'text': block_data_by_id[block_id]['field_name']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['field_id'] =  parseInt($(e.currentTarget).val())
                    redraw_chart(block_id);
                });
                
                // Operation, operation
                $(elmId+" .block_config_operation").select2({
                    tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Operation',
                    ajax: {
                        url: "api/selections/web.dashboard.block/operation", dataType: "json", type: "GET",
                        data: function (params) {
                            return {};
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.value, slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['operation'] ? {
                            'id': block_data_by_id[block_id]['operation'],
                            'text': block_data_by_id[block_id]['operation']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['operation'] =  $(e.currentTarget).val()
                    redraw_chart(block_id);
                });
                
                // Sort, sort
                $(elmId+" .block_config_sort").select2({
                    tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Sort',
                    ajax: {
                        url: "api/selections/web.dashboard.block/sort", dataType: "json", type: "GET",
                        data: function (params) {
                            return {};
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.value, slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['sort'] ? {
                            'id': block_data_by_id[block_id]['sort'],
                            'text': block_data_by_id[block_id]['sort']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['sort'] =  $(e.currentTarget).val()
                    redraw_chart(block_id);
                });
                
                // Group By, group_field_id
                $(elmId+" .block_config_group_field_id").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: ' ',
                    ajax: {
                        url: "api/list/ir.model.fields", dataType: "json", type: "GET",
                        data: function (params) {
                            var block_id = $( this ).parents('.dashboard_block').first().data("id");
                            var model_id = block_data_by_id[block_id]['model_id'];
                            return {
                                "domains": "[('ttype', 'in', ['char','date','datetime','many2one','boolean','selection']), ('store', '=', True), ('model_id', '=', " + model_id + " ), '|', ('name', 'ilike', '" + params + "'), ('field_description', 'ilike', '" + params + "')]",
                                "fields": "['id', 'field_description']"
                            };
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.field_description, slug: item.field_description, id: item.id
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['group_field_name'] ? {
                            'id': block_data_by_id[block_id]['group_field_name'],
                            'text': block_data_by_id[block_id]['group_field_name']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['group_field_id'] =  parseInt($(e.currentTarget).val())
                    redraw_chart(block_id);
                })
                
                // Sub Group By, sub_group_field_id
                $(elmId+" .block_config_subgroup_field_id").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: ' ',
                    ajax: {
                        url: "api/list/ir.model.fields", dataType: "json", type: "GET",
                        data: function (params) {
                            var block_id = $( this ).parents('.dashboard_block').first().data("id");
                            var model_id = block_data_by_id[block_id]['model_id'];
                            return {
                                "domains": "[('ttype', 'in', ['char','date','datetime','many2one','boolean','selection']), ('store', '=', True), ('model_id', '=', " + model_id + " ), '|', ('name', 'ilike', '" + params + "'), ('field_description', 'ilike', '" + params + "')]",
                                "fields": "['id', 'field_description']"
                            };
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.field_description, slug: item.field_description, id: item.id
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['subgroup_field_name'] ? {
                            'id': block_data_by_id[block_id]['subgroup_field_name'],
                            'text': block_data_by_id[block_id]['subgroup_field_name']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['subgroup_field_id'] =  parseInt($(e.currentTarget).val())
                    redraw_chart(block_id);
                });
                
                // Group Date Format, group_date_format
                $(elmId+" .block_config_group_date_format").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Date Format',
                    ajax: {
                        url: "api/selections/web.dashboard.block/group_date_format", dataType: "json", type: "GET",
                        data: function (params) {
                            return {};
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: replace_(item.value), slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['group_date_format'] ? {
                            'id': block_data_by_id[block_id]['group_date_format'],
                            'text': block_data_by_id[block_id]['group_date_format']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['group_date_format'] =  $(e.currentTarget).val()
                    redraw_chart(block_id);
                });
                
                // Sub Group Date Format, subgroup_date_format
                $(elmId+" .block_config_subgroup_date_format").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Date Format',
                    ajax: {
                        url: "api/selections/web.dashboard.block/subgroup_date_format", dataType: "json", type: "GET",
                        data: function (params) {
                            return {};
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: replace_(item.value), slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['subgroup_date_format'] ? {
                            'id': block_data_by_id[block_id]['subgroup_date_format'],
                            'text': block_data_by_id[block_id]['subgroup_date_format']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['subgroup_date_format'] =  $(e.currentTarget).val()
                    redraw_chart(block_id);
                });
                
                // Group Limit, group_limit_selection
                $(elmId+" .block_config_group_limit").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Limit',
                    ajax: {
                        url: "api/selections/web.dashboard.block/group_limit_selection", dataType: "json", type: "GET",
                        data: function (params) {
                            return {};
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.name, slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['group_limit'] ? {
                            'id': block_data_by_id[block_id]['group_limit'],
                            'text': block_data_by_id[block_id]['group_limit']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['group_limit'] =  parseInt($(e.currentTarget).val())
                    redraw_chart(block_id);
                });
                
                // SubGroup Limit, subgroup_limit_selection
                $(elmId+" .block_config_subgroup_limit").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Limit',
                    ajax: {
                        url: "api/selections/web.dashboard.block/subgroup_limit_selection", dataType: "json", type: "GET",
                        data: function (params) {
                            return {};
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.name, slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['subgroup_limit'] ? {
                            'id': block_data_by_id[block_id]['subgroup_limit'],
                            'text': block_data_by_id[block_id]['subgroup_limit']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['subgroup_limit'] =  parseInt($(e.currentTarget).val())
                    redraw_chart(block_id);
                });
                
                // Group Others, show_group_others
                $(elmId+" .block_config_show_group_others").on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['show_group_others'] =  $(e.currentTarget).is(':checked');
                    redraw_chart(block_id);
                });

                // Sub Group Others, show_subgroup_others
                $(elmId+" .block_config_show_subgroup_others").on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['show_subgroup_others'] =  $(e.currentTarget).is(':checked');
                    redraw_chart(block_id);
                });

                // Block Type, block_type
                $(elmId+" .block_config_block_type").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Type',
                    ajax: {
                        url: "api/selections/web.dashboard.block/block_type", dataType: "json", type: "GET",
                        data: function (params) {
                            return {};
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: replace_(item.value), slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['block_type'] ? {
                            'id': block_data_by_id[block_id]['block_type'],
                            'text': replace_(block_data_by_id[block_id]['block_type'])
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['block_type'] =  $(e.currentTarget).val()
                    redraw_chart(block_id);
                });
                
                // Domain Date Field, domain_date_field_id
                $(elmId+" .block_config_domain_date_field_id").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Date Filter',
                    ajax: {
                        url: "api/list/ir.model.fields", dataType: "json", type: "GET",
                        data: function (params) {
                            var block_id = $( this ).parents('.dashboard_block').first().data("id");
                            var model_id = block_data_by_id[block_id]['model_id'];
                            return {
                                "domains": "[('ttype', 'in', ['date','datetime']), ('store', '=', True), ('model_id', '=', " + model_id + " ), '|', ('name', 'ilike', '" + params + "'), ('field_description', 'ilike', '" + params + "')]",
                                "fields": "['id', 'field_description']"
                            };
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.field_description, slug: item.field_description, id: item.id
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['domain_date_field_name'] ? {
                            'id': block_data_by_id[block_id]['domain_date_field_name'],
                            'text': block_data_by_id[block_id]['domain_date_field_name']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['domain_date_field_id'] =  parseInt($(e.currentTarget).val())
                    redraw_chart(block_id);
                });
                
                // Domain Date, domain_date
                $(elmId+" .block_config_domain_date").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Date Filter',
                    ajax: {
                        url: "api/selections/web.dashboard.block/domain_date", dataType: "json", type: "GET",
                        data: function (params) {
                            return {};
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: replace_(item.value), slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['domain_date'] ? {
                            'id': block_data_by_id[block_id]['domain_date'],
                            'text': replace_(block_data_by_id[block_id]['domain_date'])
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['domain_date'] =  $(e.currentTarget).val()
                    redraw_chart(block_id);
                });
                
                // Time Calculation Method, time_calculation_method
                $(elmId+" .block_config_time_calculation_method").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: 'Calculation Method',
                    ajax: {
                        url: "api/selections/web.dashboard.block/time_calculation_method", dataType: "json", type: "GET",
                        data: function (params) {
                            return {};
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: replace_(item.value), slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['time_calculation_method'] ? {
                            'id': block_data_by_id[block_id]['time_calculation_method'],
                            'text': block_data_by_id[block_id]['time_calculation_method']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['time_calculation_method'] =  $(e.currentTarget).val()
                    redraw_chart(block_id);
                });
                
                // Domain Values, domain_values_field_id
                $(elmId+" .block_config_domain_values_field_id").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: ' ',
                    ajax: {
                        url: "api/list/ir.model.fields", dataType: "json", type: "GET",
                        data: function (params) {
                            var block_id = $( this ).parents('.dashboard_block').first().data("id");
                            var model_id = block_data_by_id[block_id]['model_id'];
                            return {
                                "domains": "[('ttype', 'in', ['char', 'many2one', 'integer', 'boolean']), ('store', '=', True), ('model_id', '=', " + model_id + " ), '|', ('name', 'ilike', '" + params + "'), ('field_description', 'ilike', '" + params + "')]",
                                "fields": "['id', 'field_description']"
                            };
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.field_description, slug: item.field_description, id: item.id
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['domain_values_field_name'] ? {
                            'id': block_data_by_id[block_id]['domain_values_field_name'],
                            'text': block_data_by_id[block_id]['domain_values_field_name']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['domain_values_field_id'] =  parseInt($(e.currentTarget).val())
                    redraw_chart(block_id);
                });
                
                // Domain Values String, domain_values_string
                $(elmId+" .block_config_domain_values_string").select2({
                    multiple: true, allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: ' ',
                    ajax: {
                        url: "api/values", dataType: "json", type: "GET",
                        data: function (params) {
                            var block_id = $( this ).parents('.dashboard_block').first().data("id");
                            var model_id = block_data_by_id[block_id]['model_id'];
                            var field_id = block_data_by_id[block_id]['domain_values_field_id'];
                            return {
                                "model_id": model_id,
                                "field_id": field_id,
                                "params": params
                            };
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.name, slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = [];
                        var domain_values_list = block_data_by_id[block_id]['domain_values_string'] ? block_data_by_id[block_id]['domain_values_string'].split(',') : [];
                        for (var i=0; i < domain_values_list.length; i++) {
                            init.push({
                                'id': domain_values_list[i],
                                'text': domain_values_list[i].replace(/'/g, '')
                            })
                        }
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['domain_values_string'] =  $(e.currentTarget).val()
                    redraw_chart(block_id);
                });
                
                // Sub Domain Values, domain_values_field_id
                $(elmId+" .block_config_subdomain_values_field_id").select2({
                    allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: ' ',
                    ajax: {
                        url: "api/list/ir.model.fields", dataType: "json", type: "GET",
                        data: function (params) {
                            var block_id = $( this ).parents('.dashboard_block').first().data("id");
                            var model_id = block_data_by_id[block_id]['model_id'];
                            return {
                                "domains": "[('ttype', 'in', ['char', 'many2one', 'integer', 'boolean']), ('store', '=', True), ('model_id', '=', " + model_id + " ), '|', ('name', 'ilike', '" + params + "'), ('field_description', 'ilike', '" + params + "')]",
                                "fields": "['id', 'field_description']"
                            };
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.field_description, slug: item.field_description, id: item.id
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = block_data_by_id[block_id]['subdomain_values_field_name'] ? {
                            'id': block_data_by_id[block_id]['subdomain_values_field_name'],
                            'text': block_data_by_id[block_id]['subdomain_values_field_name']
                        } : {};
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['subdomain_values_field_id'] =  parseInt($(e.currentTarget).val())
                    redraw_chart(block_id);
                });
                
                // Sub Domain Values String, domain_values_string
                $(elmId+" .block_config_subdomain_values_string").select2({
                    multiple: true, allowClear: true, tokenSeparators: [',', ' '], minimumResultsForSearch: 10, placeholder: ' ',
                    ajax: {
                        url: "api/values", dataType: "json", type: "GET",
                        data: function (params) {
                            var block_id = $( this ).parents('.dashboard_block').first().data("id");
                            var model_id = block_data_by_id[block_id]['model_id'];
                            var field_id = block_data_by_id[block_id]['subdomain_values_field_id'];
                            return {
                                "model_id": model_id,
                                "field_id": field_id,
                                "params": params
                            };
                        }, results: function (data) { return { results: $.map(data, function (item) { return {
                                text: item.name, slug: item.value, id: item.value
                        }})}}
                    },
                    initSelection : function (element, callback) {
                        var block_id = $( element ).parents('.dashboard_block').first().data("id");
                        var init = [];
                        var domain_values_list = block_data_by_id[block_id]['subdomain_values_string'] ? block_data_by_id[block_id]['subdomain_values_string'].split(',') : [];
                        for (var i=0; i < domain_values_list.length; i++) {
                            init.push({
                                'id': domain_values_list[i],
                                'text': domain_values_list[i].replace(/'/g, '')
                            })
                        }
                        callback(init);
                    }
                }).select2('val', []).on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['subdomain_values_string'] =  $(e.currentTarget).val()
                    redraw_chart(block_id);
                });
                
                // Config Header
                $(elmId+" .config_toggle").click(function() {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    reset_block_data(block_id);
                    // redraw_chart(block_id);
                    $(".dashboard_block:not("+"#block_" + block_id+") .block_config.open .block_config_content").slideUp( "slow", function() {
                        $(".dashboard_block:not("+"#block_" + block_id+") .block_config.open .block_config_content").hide();
                        $(".dashboard_block:not("+"#block_" + block_id+") .block_config.open").removeClass("open");
                    });
                    if ($("#block_" + block_id + " .block_config_content").is(":visible")) {
                        $("#block_" + block_id + " .block_config_content").slideUp( "slow", function() {
                            $("#block_" + block_id + " .block_config_content").hide();
                            $("#block_" + block_id + " .block_config").removeClass("open");
                        });
                    } else {
                        $("#block_" + block_id + " .block_config").addClass("open");
                        $("#block_" + block_id + " .block_config_content").slideDown( "slow", function() {
                            $("#block_" + block_id + " .block_config_content").show()
                        });
                    }  
                });
                $(elmId+" .config_detail").click(function() {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    window.open("/web#id=" + block_id + "&model=web.dashboard.block&view_type=form", '_blank');
                });
                $(elmId+" .config_save").click(function() {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    redraw_chart(block_id, true);
                    if ($("#block_" + block_id + " .block_config_content").is(":visible")) {
                        $("#block_" + block_id + " .block_config_content").slideUp( "slow", function() {
                            $("#block_" + block_id + " .block_config_content").hide()
                        });
                    } 
                });
                $(elmId+" .expand_toggle").click(function() {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    if (block_data_by_id[block_id]['block_size'] == '1col') {
                        $('.block_chart#block_'+block_id + ' .block_chart_content').empty();
                        $(elmId+' #block_'+block_id).removeClass('block_1col')
                        $(elmId+' #block_'+block_id).removeClass('float_expand')
                        $(elmId+' #block_'+block_id).addClass('block_'+reset_block_data_by_id[block_id]['block_size'])
                        block_data_by_id[block_id]['block_size'] = reset_block_data_by_id[block_id]['block_size'];
                        $('.block_chart:not(#block_'+block_id+')').fadeIn();
                    } else {
                        $('.block_chart#block_'+block_id + ' .block_chart_content').empty();
                        $(elmId+' #block_'+block_id).removeClass('block_'+reset_block_data_by_id[block_id]['block_size'])
                        $(elmId+' #block_'+block_id).addClass('block_1col')
                        $(elmId+' #block_'+block_id).addClass('float_expand')
                        block_data_by_id[block_id]['block_size'] =  '1col';
                        $('.block_chart:not(#block_'+block_id+')').fadeOut();
                    }
                    redraw_chart(block_id);
                });
                $(elmId+" .reset_toggle").click(function() {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    reset_block_data(block_id);
                    redraw_chart(block_id);
                });

                // Name Change
                $(elmId+" input.block_text").on("change", function (e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    block_data_by_id[block_id]['name'] =  $(e.currentTarget).val()
                });

                // Click Chart Action
                $(elmId+" .block_chart_content").on("click", ".ct-bar, .ct-point, .ct-slice-pie, .ct-slice-donut", function(e) {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    e.stopPropagation();
                    if (block_data_by_id[block_id]['filter_queries'])
                        block_data_by_id[block_id]['filter_queries'] = block_data_by_id[block_id]['filter_queries'] + ' AND ' + $(elmId+' #block_'+block_id+" .block_chart_content .chartist-tooltip .filter_queries").text();
                    else
                        block_data_by_id[block_id]['filter_queries'] = $(elmId+' #block_'+block_id+" .block_chart_content .chartist-tooltip .filter_queries").text();

                    var action_title = $(elmId+' #block_'+block_id+" .block_chart_content .chartist-tooltip .action_title").text();
                    var action_group_field_id = $(elmId+' #block_'+block_id+" .block_chart_content .chartist-tooltip .action_group_field_id").text();
                    var action_group_block_type = $(elmId+' #block_'+block_id+" .block_chart_content .chartist-tooltip .action_group_block_type").text();
                    block_data_by_id[block_id]['name'] = block_data_by_id[block_id]['title'] + ' : ' + action_title;
                    if (action_group_field_id && action_group_field_id.length)
                        block_data_by_id[block_id]['group_field_id'] = parseInt(action_group_field_id);
                    if (action_group_block_type && action_group_block_type.length)
                        block_data_by_id[block_id]['block_type'] = action_group_block_type;
                    // $(elmId+' #block_'+block_id+" .block_subtitle").text(action_title);
                    // console.log("Click Data", block_data_by_id[block_id]);
                    redraw_chart(block_id);
                })

                // Show List Action
                $(elmId+" .list_toggle").click(function() {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    open_list(block_id);
                })
                
                // Action Button
                $(elmId+" .block_float_button").click(function() {
                    var block_id = $( this ).parents('.dashboard_block').first().data("id");
                    open_action(block_id);
                })
            }
            var init_date_configuration = function(block) {
                var elmId = "#block_"+block['id']
                if(block['group_field_ttype'] == 'date' || block['group_field_ttype'] == 'datetime')
                    $(elmId + " .block_config_group_date_format").show()
                else
                    $(elmId + " .block_config_group_date_format").hide()
                if(block['subgroup_field_ttype'] == 'date' || block['subgroup_field_ttype'] == 'datetime')
                    $(elmId + " .block_config_subgroup_date_format").show()
                else
                    $(elmId + " .block_config_subgroup_date_format").hide()
            }
            var init_configuration = function(block) {
                var elmId = "#block_"+block['id']
                if(block['group_field_ttype'] == 'date' || block['group_field_ttype'] == 'datetime')
                    $(elmId + " .block_config_group_date_format").show()
                else
                    $(elmId + " .block_config_group_date_format").hide()
                if(block['subgroup_field_ttype'] == 'date' || block['subgroup_field_ttype'] == 'datetime')
                    $(elmId + " .block_config_subgroup_date_format").show()
                else
                    $(elmId + " .block_config_subgroup_date_format").hide()
                $(elmId + " .block_config_show_group_others").attr("checked", block['show_group_others']);
                $(elmId + " .block_config_show_subgroup_others").attr("checked", block['show_subgroup_others']);
            }
            var open_config = function(elmId){
                if (!$(elmId + " .block_config_content").is(":visible")) {
                    $(elmId + " .block_config").addClass("open");
                    $(elmId + " .block_config_content").slideDown( "slow", function() {
                        $(elmId + " .block_config_content").show();
                    });
                } 
            }
            var replace_ = function(init_string){
                if (init_string)
                    return init_string.replace(/_/g, ' ');
                return '';
            }
            var init_chart = function(block_data, block_id, elmId) {
                var link_block;
                var block_elm;
                if (block_data['block_type'] == 'tile') {
                    var block_tile = $('#block_tile_template').clone();
                    block_tile.addClass('block_'+block_data['block_size'])
                    block_tile.attr('id', 'block_'+block_id);
                    block_tile.data('id', block_id);
                    block_tile.show();

                    if ($('.block_'+block_data['block_size']).length)
                        block_tile.insertAfter('.block_'+block_data['block_size']+':last');
                    else {
                        $('.block_row:last').append('<div style="clear:both"></div>');
                        $('.o_dashboard_view').append('<div class="block_row"></div>');
                        block_tile.appendTo('.block_row:last');
                    }

                    if ('menu_id' in block_data && block_data['menu_id'] != '')
                        link_block = '/web#menu_id='+block_data['menu_id'];
                    if ('link' in block_data && block_data['link'] != '')
                        link_block = block_data['link'];

                    block_elm = draw_chart(block_data['block_type'], elmId, block_data);
                    draw_action_button(elmId, block_data);
                } else {
                    var block_chart = $('#block_chart_template').clone();
                    block_chart.addClass('block_'+block_data['block_size'])
                    block_chart.attr('id', 'block_'+block_id);
                    block_chart.data('id', block_id);
                    block_chart.show();

                    if ($('.block_'+block_data['block_size']).length)
                        block_chart.insertAfter('.block_'+block_data['block_size']+':last');
                    else {
                        $('.block_row:last').append('<div style="clear:both"></div>');
                        $('.o_dashboard_view').append('<div class="block_row"></div>');
                        block_chart.appendTo('.block_row:last');
                    }

                    if ('menu_id' in block_data && block_data['menu_id'] != '')
                        link_block = '/web#menu_id='+block_data['menu_id'];
                    if ('link' in block_data && block_data['link'] != '')
                        link_block = block_data['link'];

                    block_elm = draw_chart(block_data['block_type'], elmId, block_data);
                    draw_action_button(elmId, block_data);
                }
                return [link_block, block_elm];
            }
            var open_action = function(block_id) {
                var data = block_data_by_id[block_id];
                if (data['action_dashboard_id']) {
                    if($('#dashboard_selection').val() != data['action_dashboard_id']) {
                        $('#dashboard_selection').val(data['action_dashboard_id']).trigger('change');
                    }
                } else if (link_dom_id[block_id]) {
                    window.open(link_dom_id[block_id], '_blank');
                }
            }
            var open_list = function(block_id) {
                var data = block_data_by_id[block_id];
                var context = "{}";
                if ('group_field' in data && data['group_field'] && data['action_group_list_view']) {
                    context = "{ 'group_by' : '"+data['group_field']+"' }"
                    if ('subgroup_field' in data && data['subgroup_field']) {
                        context = "{ 'group_by' : ['"+data['subgroup_field']+"', '"+data['group_field']+"'] }"
                    }
                }
                var domain = [];
                if ('domain_date_field' in data && data['domain_date_field']) {
                    domain.push([data['domain_date_field'], '>=', data['start_date']]);
                    domain.push([data['domain_date_field'], '<=', data['end_date']]);
                }
                if ('domain_values_field' in data && 'domain_values_string' in data && data['domain_values_field'] && data['domain_values_string']) {
                    var domain_values_array_string = data['domain_values_string'].split(',');
                    for (var i=0; i<domain_values_array_string.length;i++){
                        if (Number(domain_values_array_string[i]))
                            domain_values_array_string[i] = Number(domain_values_array_string[i])
                        else
                            domain_values_array_string[i] = domain_values_array_string[i].replace(/'/g, "")

                    }
                    domain.push([data['domain_values_field'], 'in', domain_values_array_string]);
                    if ('subdomain_values_field' in data && 'subdomain_values_string' in data  && data['subdomain_values_field'] && data['subdomain_values_string']) {
                        var subdomain_values_array_string = data['subdomain_values_string'].split(',');
                        for (var i=0; i<subdomain_values_array_string.length;i++){
                            if (Number(subdomain_values_array_string[i]))
                                subdomain_values_array_string[i] = Number(subdomain_values_array_string[i])
                            else
                                subdomain_values_array_string[i] = subdomain_values_array_string[i].replace(/'/g, "")
                        }
                        domain.push([data['subdomain_values_field'], 'in', subdomain_values_array_string]);
                    }
                }
                self.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Dashboard Detail',
                    res_model: block_data_by_id[block_id]['model'],
                    views: [[false, "list"], [false, "form"]],
                    view_type: 'list',
                    view_mode: 'list',
                    target: 'current',
                    context: context,
                    domain: domain,
                });
            }
            var reset_block_data = function(block_id) {
                block_data_by_id[block_id] = JSON.parse(JSON.stringify(reset_block_data_by_id[block_id]));
            }
            var get_dashboard = function(dashboard_id, iteration_value=false) { 
                var dashboard_url = iteration_value ? dashboard_id + "/" + iteration_value : dashboard_id;
                $.get("api/dashboard/"+dashboard_url, function(data, status){
                    console.log("Data: ", data, "\nStatus: ", status);
                    $('#loading').hide();
                    if (!data.length)
                        $('#empty_dashboard_message').show();
                    for (var i=0; i < data.length; i++) {
                        var block_data = data[i];
                        var block_id = block_data['id'];
                        var elmId = '#block_'+block_id;
                        block_data_by_id[block_id] = block_data
                        if (!reset_block_data_by_id[block_id])
                            reset_block_data_by_id[block_id] = JSON.parse(JSON.stringify(block_data))
                        var return_init_chart = init_chart(block_data, block_id, elmId)
                        link_dom_id[block_id] = return_init_chart[0]
                        block_elm_by_id[block_id] = return_init_chart[1]
                        // Error
                        $(elmId + " .block_error").hide()
                        if ('error' in block_data) {
                            $(elmId + " .block_error").show().text(block_data['error'])
                        }
                    }
                    render_configuration(".o_dashboard_view");
                    for (var i=0; i < data.length; i++) {
                        var block_data = data[i];
                        init_configuration(block_data);
                    }
                    $('.block_row:last').append('<div style="clear:both"></div>');
                    $('.block_tile_content h1').click(function() {
                        var block_id = $( this ).parents('.dashboard_block').first().data("id");
                        open_list(block_id);
                    })
                    $('[data-toggle="tooltip"]').tooltip();  
                })
                .fail(function(data) {
                  alert(data['responseText']);
                });
            };
            get_dashboard(dashboard_id);
            $('.new_block').click(function() {
                var block_size;
                if ($(this).hasClass('new_block_2col')) block_size = '2col';
                if ($(this).hasClass('new_block_3col')) block_size = '3col';
                if ($(this).hasClass('new_block_4col')) block_size = '4col';
                if (block_size) {
                    $.get("api/dashboard/new_block/"+dashboard_id+"/"+block_size, function(data, status){
                        console.log("Data: ", data, "\nStatus: ", status);
                        var block_data = data;
                        var block_id = block_data['id'];
                        var elmId = '#block_'+block_id;
                        block_data_by_id[block_id] = block_data
                        var return_init_chart = init_chart(block_data, block_id, elmId)
                        link_dom_id[block_id] = return_init_chart[0]
                        block_elm_by_id[block_id] = return_init_chart[1]
                        render_configuration(elmId);
                        init_configuration(block_data);
                        $('#empty_dashboard_message').hide();
                    });
                }
            });
            var open_dashboard = function(dashboard_id) {
                $('#empty_dashboard_message').hide();
                $('.block_row').remove();
                $('#tableau_container').remove();
                $('.o_dashboard_view').append('<div id="tableau_container"></div>');
                $('.o_dashboard_view').append('<div class="block_row"></div>');

                if (dashboard_by_id[dashboard_id]['dashboard_source'] == 'tableau') {
                    console.log(dashboard_by_id, dashboard_id);
                    var containerDiv = document.getElementById("tableau_container"),
                    url = dashboard_by_id[dashboard_id]['tableau_url'];

                    var viz = new tableau.Viz(containerDiv, url);
                    $('#tableau_container').show();
                } else {
                    get_dashboard(dashboard_id, dashboard_by_id[dashboard_id]['iteration_value']);
                }
            }
            $( '#dashboard_selection' ).change(function() {
                $( '#dashboard_selection option:selected' ).each(function() {
                    dashboard_id = $( this ).val();
                });
                open_dashboard(dashboard_id);
            })
        }, TIMEOUT);
    },
    destroy: function() {
        console.log("Destroy");
        this._super.apply(this, arguments);
    },
    chartArea: function(self, elmId, data) {
        return self.chartLine(self, elmId, data, true);
    },
    chartLine: function(self, elmId, data, showArea=false) {
        self.setChartTitle(self, elmId, data);
        var chart = new Chartist.Line(elmId+CHARTCONTENTDOM, data, {
            fullWidth: true,
            showArea: showArea,
            chartPadding: {
                right: 40
            },
            axisY: {
                labelInterpolationFnc: function(value) {
                    if (value >= 1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value >= 1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value >= 10 * 1000)
                        return value / 1000 + ' nghìn'
                    else if (value <= -1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value <= -1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value <= -10 * 1000)
                        return value / 1000 + ' nghìn'
                    return value;
                }
            },
            plugins: [
                Chartist.plugins.legend({
                    legendNames: data['legends'],
                }),
                Chartist.plugins.tooltip({
                    metaIsHTML: true,
                    tooltipOffset: {
                        y : 50
                    }
                }),
                Chartist.plugins.ctAxisTitle({
                  axisX: {
                    axisTitle: _t('Theo ')+data['group_field_name'],
                    axisClass: 'ct-axis-title',
                    textAnchor: 'middle'
                  },
                })
            ],
            // low: 0
        });
          
        // Let's put a sequence number aside so we can use it in the event callbacks
        var seq = 0,
        delays = 80,
        durations = 500;
        
        // Once the chart is fully created we reset the sequence
        // chart.on('created', function() {
        //  seq = 0;
        // });
        
        // On each drawn element by Chartist we use the Chartist.Svg API to trigger SMIL animations
        chart.on('draw', function(data) {
            seq++;
            
            if(data.type === 'line') {
                // If the drawn element is a line we do a simple opacity fade in. This could also be achieved using CSS3 animations.
                data.element.animate({
                opacity: {
                    // The delay when we like to start the animation
                    begin: seq * delays + 1000,
                    // Duration of the animation
                    dur: durations,
                    // The value where the animation should start
                    from: 0,
                    // The value where it should end
                    to: 1
                }
                });
            } else if(data.type === 'label' && data.axis === 'x') {
                data.element.animate({
                y: {
                    begin: seq * delays,
                    dur: durations,
                    from: data.y + 100,
                    to: data.y,
                    // We can specify an easing function from Chartist.Svg.Easing
                    easing: 'easeOutQuart'
                }
                });
            } else if(data.type === 'label' && data.axis === 'y') {
                data.element.animate({
                x: {
                    begin: seq * delays,
                    dur: durations,
                    from: data.x - 100,
                    to: data.x,
                    easing: 'easeOutQuart'
                }
                });
            } else if(data.type === 'point') {
                data.element.animate({
                x1: {
                    begin: seq * delays,
                    dur: durations,
                    from: data.x - 10,
                    to: data.x,
                    easing: 'easeOutQuart'
                },
                x2: {
                    begin: seq * delays,
                    dur: durations,
                    from: data.x - 10,
                    to: data.x,
                    easing: 'easeOutQuart'
                },
                opacity: {
                    begin: seq * delays,
                    dur: durations,
                    from: 0,
                    to: 1,
                    easing: 'easeOutQuart'
                }
                });
            } else if(data.type === 'grid') {
                // Using data.axis we get x or y which we can use to construct our animation definition objects
                var pos1Animation = {
                begin: seq * delays,
                dur: durations,
                from: data[data.axis.units.pos + '1'] - 30,
                to: data[data.axis.units.pos + '1'],
                easing: 'easeOutQuart'
                };
            
                var pos2Animation = {
                begin: seq * delays,
                dur: durations,
                from: data[data.axis.units.pos + '2'] - 100,
                to: data[data.axis.units.pos + '2'],
                easing: 'easeOutQuart'
                };
            
                var animations = {};
                animations[data.axis.units.pos + '1'] = pos1Animation;
                animations[data.axis.units.pos + '2'] = pos2Animation;
                animations['opacity'] = {
                begin: seq * delays,
                dur: durations,
                from: 0,
                to: 1,
                easing: 'easeOutQuart'
                };
            
                data.element.animate(animations);
            }
        });
        return chart;
    },
    chartBar: function(self, elmId, data) {
        self.setChartTitle(self, elmId, data);
        var chart = new Chartist.Bar(elmId+CHARTCONTENTDOM, data, {
            fullWidth: true,
            chartPadding: {
                right: 40
            },
            axisY: {
                labelInterpolationFnc: function(value) {
                    if (value >= 1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value >= 1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value >= 10 * 1000)
                        return value / 1000 + ' nghìn'
                    else if (value <= -1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value <= -1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value <= -10 * 1000)
                        return value / 1000 + ' nghìn'
                    return value;
                }
            },
            plugins: [
                Chartist.plugins.legend({
                    legendNames: data['legends'],
                }),
                Chartist.plugins.tooltip({
                    metaIsHTML: true,
                    tooltipOffset: {
                        y : 50
                    }
                }),
                Chartist.plugins.ctAxisTitle({
                  axisX: {
                    axisTitle: _t('Theo ')+data['group_field_name'],
                    axisClass: 'ct-axis-title',
                    textAnchor: 'middle'
                  },
                })
            ]
        });

        chart.on('draw', function(data) {
            if(data.type == 'bar') {
                data.element.animate({
                    y2: {
                        dur: '1s',
                        from: data.y1,
                        to: data.y2
                    }
                });
            }
        });
        return chart
    },
    chartHBar: function(self, elmId, data) {
        self.setChartTitle(self, elmId, data);
        var chart = new Chartist.Bar(elmId+CHARTCONTENTDOM, data, {
            horizontalBars: true,
            axisX: {
                labelInterpolationFnc: function(value) {
                    if (value >= 1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value >= 1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value >= 10 * 1000)
                        return value / 1000 + ' nghìn'
                    else if (value <= -1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value <= -1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value <= -10 * 1000)
                        return value / 1000 + ' nghìn'
                    return value;
                }
            },
            axisY: {
              offset: 70
            },
            plugins: [
                Chartist.plugins.legend({
                    legendNames: data['legends'],
                }),
                Chartist.plugins.tooltip({
                    metaIsHTML: true,
                    tooltipOffset: {
                        y : 50
                    }
                })
            ]
        });

        chart.on('draw', function(data) {
            if(data.type == 'bar') {
                data.element.animate({
                    x2: {
                        dur: '1s',
                        from: data.x1,
                        to: data.x2
                    }
                });
            }
        });
        return chart
    },
    chartLineTreshold: function(self, elmId, data) {
        self.setChartTitle(self, elmId, data);
        var chart = Chartist.Line(elmId+CHARTCONTENTDOM, data, {
            showArea: true,
            axisY: {
                labelInterpolationFnc: function(value) {
                    if (value >= 1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value >= 1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value >= 10 * 1000)
                        return value / 1000 + ' nghìn'
                    else if (value <= -1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value <= -1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value <= -10 * 1000)
                        return value / 1000 + ' nghìn'
                    return value;
                }
            },
            plugins: [
              Chartist.plugins.ctThreshold({
                threshold: data['threshold']
              })
            ]
        });
        return chart;
    },
    chartDonut: function(self, elmId, data) {
        self.setChartTitle(self, elmId, data);
        var total = 0;
        var series = data['series'];
        for (var i=0; i<series.length; i++) {
            total += series[i]['value'];
        }
        var chart = Chartist.Pie(elmId+CHARTCONTENTDOM, data, {
            donut: true,
            showLabel: true,
            labelInterpolationFnc: function(label, index) {
                var value = series[index]['value'];
                index++;
                return Math.round(value / total * 100) + '%';
            },
            plugins: [
                Chartist.plugins.legend({
                    legendNames: data['legends'],
                }),
                Chartist.plugins.tooltip({
                    metaIsHTML: true,
                    tooltipOffset: {
                        y : 50
                    }
                })
            ]
        });
        
        chart.on('draw', function(data) {
            if(data.type === 'slice') {
                // Get the total path length in order to use for dash array animation
                var pathLength = data.element._node.getTotalLength();
            
                // Set a dasharray that matches the path length as prerequisite to animate dashoffset
                data.element.attr({
                'stroke-dasharray': pathLength + 'px ' + pathLength + 'px'
                });
            
                // Create animation definition while also assigning an ID to the animation for later sync usage
                var animationDefinition = {
                'stroke-dashoffset': {
                    id: 'anim' + data.index,
                    dur: 1000,
                    from: -pathLength + 'px',
                    to:  '0px',
                    easing: Chartist.Svg.Easing.easeOutQuint,
                    // We need to use `fill: 'freeze'` otherwise our animation will fall back to initial (not visible)
                    fill: 'freeze'
                }
                };
            
                // If this was not the first slice, we need to time the animation so that it uses the end sync event of the previous animation
                if(data.index !== 0) {
                animationDefinition['stroke-dashoffset'].begin = 'anim' + (data.index - 1) + '.end';
                }
            
                // We need to set an initial value before the animation starts as we are not in guided mode which would do that for us
                data.element.attr({
                'stroke-dashoffset': -pathLength + 'px'
                });
            
                // We can't use guided mode as the animations need to rely on setting begin manually
                // See http://gionkunz.github.io/chartist-js/api-documentation.html#chartistsvg-function-animate
                data.element.animate(animationDefinition, false);
            }
        });
        
        // For the sake of the example we update the chart every time it's created with a delay of 8 seconds
        // chart.on('created', function() {
        //     index = 0;
        //     if(anim) {
        //         clearTimeout(anim);
        //         anim = null;
        //     }
        //     var anim = setTimeout(chart.update.bind(chart), 10000);
        // });

        return chart;
    },
    chartStackBar: function(self, elmId, data) {
        self.setChartTitle(self, elmId, data);
        return Chartist.Bar(elmId+CHARTCONTENTDOM, data, {
            stackBars: true,
            axisY: {
                labelInterpolationFnc: function(value) {
                    if (value >= 1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value >= 1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value >= 10 * 1000)
                        return value / 1000 + ' nghìn'
                    else if (value <= -1000 * 1000 * 1000)
                        return value / (1000 * 1000 * 1000) + ' tỷ'
                    else if (value <= -1000 * 1000)
                        return value / (1000 * 1000) + ' triệu'
                    else if (value <= -10 * 1000)
                        return value / 1000 + ' nghìn'
                    return value;
                }
            },
            plugins: [
                Chartist.plugins.legend({
                    legendNames: data['legends'],
                }),
                Chartist.plugins.tooltip({
                    metaIsHTML: true,
                    tooltipOffset: {
                        y : 50
                    }
                }),
                Chartist.plugins.ctAxisTitle({
                  axisX: {
                    axisTitle: _t('Theo ')+data['group_field_name'],
                    axisClass: 'ct-axis-title',
                    textAnchor: 'middle'
                  },
                })
            ]}).on('draw', function(data) {
                if(data.type === 'bar') {
                    data.element.attr({
                        style: 'stroke-width: 20px'
                    });
                }
            }
        );
    },
    chartPie: function(self, elmId, data){
        self.setChartTitle(self, elmId, data);
        var total = 0;
        var series = data['series'];
        for (var i=0; i<series.length; i++) {
            total += series[i]['value'];
        }
        var chart = Chartist.Pie(elmId+CHARTCONTENTDOM, data, {
            labelInterpolationFnc: function(label, index) {
                var value = series[index]['value'];
                index++;
                return Math.round(value / total * 100) + '%';
            },
            plugins: [
                Chartist.plugins.legend({
                    legendNames: data['legends'],
                }),
                Chartist.plugins.tooltip({
                    metaIsHTML: true,
                    tooltipOffset: {
                        y : 50
                    }
                })
            ]
        });

        return chart;
    },
    setChartTitle: function(self, elmId, data) {
        self.$el.find(elmId+CHARTTITLEDOM).val(data['title']);
    },
    setTile: function(self, elmId, data) {
        var string_length = data['value'].length + data['uom'].length;
        var font_size = 60 - (string_length - 4)/2*10;
        if ('background' in data && data['background'] != '')
            self.$el.find(elmId).css({"background":data['background']});
        self.$el.find(elmId+TILEH1DOM).css({"font-size":font_size+"px"});
        self.$el.find(elmId+TILEICONDOM).addClass(data['icon']);
        self.$el.find(elmId+TILEVALUEDOM).text(data['value']);
        self.$el.find(elmId+TILEUOMDOM).text(data['uom']);
        self.$el.find(elmId+TILEDESCDOM).val(data['desc']);
        if (data['color'])
            self.$el.find(elmId).attr('style','background: '+ data['color']);
        return self.$el.find(elmId);
    }
});

});
