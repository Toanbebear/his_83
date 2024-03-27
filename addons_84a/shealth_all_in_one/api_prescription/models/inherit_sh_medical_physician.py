from datetime import date
import json

import requests

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class InheritPhysician(models.Model):
    _inherit = "sh.medical.physician"

    account_prescription = fields.Char('Tài khoản', help='Tài khoản đăng nhập đơn thuốc Điện tử')
    pass_prescription = fields.Char('Mật khẩu', help='Mật khẩu đăng nhập đơn thuốc Điện tử')
    code_connected = fields.Char('Mã liên thông', help='Mã liên thông bác sĩ')
    token_his_physician = fields.Char('Token', help='token bác sĩ')

    def get_token_83(self):
        if self.institution.login and self.institution.password and self.institution.url_prescription:
            url = self.institution.url_prescription
            login = self.institution.login
            password = self.institution.password
            payload = json.dumps({
                "username": login,
                "password": password,
            })
            headers = {
                'username': login,
                'password': password,
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            response = response.json()
            if response['token']:
                self.token_his_physician = response['token']
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Thành công')
                    }
                }
            else:
                raise ValidationError(_('Không tìm thấy dữ liệu. Yêu cầu điền lại đúng thông tin'))
        else:
            raise ValidationError(_('Chưa điền đủ thông tin'))