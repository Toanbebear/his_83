odoo.define('shealth_all_in_one.BasicController', function (require) {
"use strict";

    var BasicController = require('web.BasicController');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var _t = core._t;

    BasicController.include({
        canBeDiscarded: function (recordID) {
            if (!this.isDirty(recordID)) {
                return $.when(false);
            }

            var model_change = recordID.split("_")[0];
            if(model_change == this.modelName){
                var message = _t("Bản ghi đã được sửa đổi, các thay đổi của bạn sẽ bị mất. Bạn có muốn tiếp tục?");
            }else{
                var message = _t("Bản ghi đã được sửa đổi và các giá trị bạn nhập đang không hợp lệ (các trường bôi đỏ). Bạn có muốn hủy bỏ bản ghi đang lỗi này?");
            }

            var def = $.Deferred();
            var dialog = Dialog.confirm(this, message, {
                title: _t("Thông báo"),
                confirm_callback: def.resolve.bind(def, true),
                cancel_callback: def.reject.bind(def),
            });
            dialog.on('closed', def, def.reject);
            return def;
        },
    });
});
	
