odoo.define('report_pdf_print.report', function (require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
    var core = require('web.core');
    var crash_manager = require('web.crash_manager');
    var framework = require('web.framework');


    var _t = core._t;
    var _lt = core._lt;

    var wkhtmltopdf_state;

    ActionManager.include({
        _executeReportAction: function (action, options) {
            var self = this;
            action = _.clone(action);

            // Only valid for pdf report.
            if (action.report_type === 'qweb-pdf') {
                return this.call('report', 'checkWkhtmltopdf').then(function (state) {
                    var active_ids_path = '/' + action.context.active_ids.join(',');
                    var url = '/report/pdf/' + action.report_name + active_ids_path;

                    printJS({printable: url, type:'pdf', showModal:true, modalMessage:_t('Retrieve content...')});
                    
                    framework.unblockUI();
                });

            } else {
                return self._super(action, options);
            }

        }
    });

});