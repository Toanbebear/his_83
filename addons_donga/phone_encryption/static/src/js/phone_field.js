odoo.define('phone_encryption.PhoneField', function (require) {
"use strict";

const basicFields = require('web.basic_fields');
const core = require('web.core');
const config = require('web.config');
var Dialog = require('web.Dialog');
var session = require('web.session');
const Phone = basicFields.FieldPhone;
const _t = core._t;

var ajax = require('web.ajax');
if (config.device.isMobile) {
    return;
}
Phone.include({
    init: function (){
        this._super.apply(this, arguments);
        this.get_token = {};
        this.cs_window = false;
        this.encrypt_phone = session.encrypt_phone;
    },
    _renderReadonly: function () {
        var def = this._super.apply(this, arguments);
        var maskPhone;
        if (this.encrypt_phone == 'True'){
            maskPhone = this.maskPhoneNumber(this.value);
        } else{
            maskPhone = this.value;
        }
        this.$el.html(maskPhone);
    },

    maskPhoneNumber: function (phoneNumber) {
      // Kiểm tra xem số điện thoại có đủ 10 chữ số không
      if (phoneNumber.length >= 10) {
        // Sử dụng phép cắt để lấy 4 số cuối
        var lastFourDigits = phoneNumber.slice(5);

        // Tạo chuỗi "xxxxx" có độ dài bằng với 5 số cuối
        var mask = "x".repeat(lastFourDigits.length);

        // Thay thế 4 số cuối bằng chuỗi "xxxx"
        var maskedNumber = phoneNumber.slice(0, 5) + mask;

        return maskedNumber;
      } else {
        // Trả về số điện thoại không thay đổi nếu không đủ 10 chữ số
        return phoneNumber;
      }
    }
});

});
