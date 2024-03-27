odoo.define('shealth_all_in_one.BasicView', function (require) {
"use strict";

    var session = require('web.session');
    var BasicView = require('web.BasicView');
    BasicView.include({
            init: function(viewInfo, params) {
                var self = this;
                this._super.apply(this, arguments);
                var model = self.controllerParams.modelName in ['res.partner','product.template'] ? 'True' : 'False';
                if(model) {
                    session.user_has_group('shealth_all_in_one.group_sh_medical_manager').then(function(has_group) {
                        if(!has_group) {
                            self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
                        }
                    });
                }
            },
    });
});
