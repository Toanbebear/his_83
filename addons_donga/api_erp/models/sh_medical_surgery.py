# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.exceptions import UserError
import requests
from odoo.exceptions import ValidationError


class ShMedicalSurgery(models.Model):
    _inherit = 'sh.medical.surgery'

    def open_form_get_surgery_erp(self):
        erp_url = self.env['ir.config_parameter'].sudo().get_param('api_erp.erp_url')
        # url = "http://localhost:13000/api/83/v1/get-surgery-ids/0918880339"
        if self.patient.phone:
            url = erp_url + '/api/83/v1/get-surgery-ids/%s' % self.patient.phone
        else:
            raise ValidationError("Bệnh nhân chưa có số điện thoại!")
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        domain = []

        record_check = self.env['sh.medical.surgery.erp'].sudo().search([('surgery_83', '=', self.id)])
        check_dict = []
        for rc in record_check:
            check_dict.append(rc.surgery_id)
            domain.append(rc.id)

        if 'data' in response and response['data']:
            for res in response['data']:
                # if 1 == 1:
                if res['surgery_id'] and int(res['surgery_id']) not in check_dict:
                    record = self.env['sh.medical.surgery.erp'].sudo().create({
                        'surgery_83': self.id,
                        'walkin_id': res['walkin_id'],
                        'walkin_name': res['walkin_name'],
                        'surgery_id': res['surgery_id'],
                        'surgery_name': res['surgery_name'],
                        'service_patient_erp': res['service_patient_erp'],
                        'name_patient_erp': res['name_patient_erp'],
                        'surgery_date': res['surgery_date'],
                    })
                    domain.append(record.id)
        view = {
            'name': 'Danh sách phiếu thủ thuật ERP',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('api_erp.view_sh_medical_surgery_erp_tree').id,
            'res_model': 'sh.medical.surgery.erp',
            'context': {},
            'domain': [('id', '=', domain)],
        }
        return view


class ShMedicalSurgeryERPFormLine(models.Model):
    _name = 'sh.medical.surgery.erp'

    surgery_83 = fields.Many2one('sh.medical.surgery', string='Phiếu 83')
    # form_id = fields.One2many('sh.medical.surgery.erp.form', 'surgery_83', string='Phiếu 83')
    surgery_date = fields.Date('Ngày bệnh nhân làm dịch vụ')
    name_patient_erp = fields.Char('Tên bệnh nhân')
    service_patient_erp = fields.Char('Dịch vụ')
    walkin_id = fields.Integer('ID phiếu khám')
    walkin_name = fields.Char('Mã phiếu khám erp')
    surgery_id = fields.Integer('ID phiếu thủ thuật')
    surgery_name = fields.Char('Mã phiếu thủ thuật erp')
    sync = fields.Boolean('Đã đồng bộ')
    payload = fields.Text('Payload')

    def sync_erp(self):
        erp_url = self.env['ir.config_parameter'].sudo().get_param('api_erp.erp_url')
        # url = "http://localhost:13000/api/83/v1/get-surgery/3092"
        if self.surgery_id:
            url = erp_url + "/api/83/v1/get-surgery/%s" % str(self.surgery_id)
        else:
            raise ValidationError("Không lấy được ID ERP phiếu thủ thuật, liên hệ Admin để hỗ trợ!")
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        if 'data' in response and response['data']:
            data = response['data']
            # check mã vật tư
            supplies_erp = data['supplies_code']
            supplies_83 = self.env['sh.medical.medicines'].sudo().search([('default_code', 'in', supplies_erp)])
            s83 = [x.default_code for x in supplies_83]
            s_missing = [x for x in supplies_erp if x not in s83]
            # bỏ toàn bộ vật tư
            self.surgery_83.sudo().sudo().write({
                'supplies': [(5,)]
            })

            dict_sup_83 = dict((s['default_code'], s['id']) for s in supplies_83)
            line_sup_id = []
            for sup in data['supplies']:
                if sup['supply_code'] in dict_sup_83:
                    line_sup_id.append((0, 0, {
                        'supply': dict_sup_83[sup['supply_code']],
                        'qty_used': int(sup['qty_used']),
                        'uom_id': self.env['sh.medical.medicines'].sudo().browse(int(dict_sup_83[sup['supply_code']])).uom_id.id if self.env['sh.medical.medicines'].sudo().browse(int(dict_sup_83[sup['supply_code']])) else False,
                        'location_id': self.surgery_83.operating_room.location_medicine_stock.id if self.env['sh.medical.medicines'].sudo().browse(int(dict_sup_83[sup['supply_code']])).medicament_type == 'Medicine' else self.surgery_83.operating_room.location_supply_stock.id,
                    }))

            # add lại vật tư theo data của erp
            # TODO cập nhật thêm trường nào thì viết vào đây
            self.surgery_83.sudo().write({
                'supplies': line_sup_id,
                'date_requested': data['date_requested'],
                'surgery_date': data['surgery_date'],
                'surgery_end_date': data['surgery_end_date'],
                'anesthetist_type': data['anesthetist_type'] if data['anesthetist_type'] else 'me',
                'surgery_type': data['surgery_type'] if data['surgery_type'] else '2',
            })

            self.sync = True
            self.payload = data
            # xóa bản ghi không dùng
            self.env['sh.medical.surgery.erp'].sudo().search(
                [('surgery_83', '=', self.surgery_83.id), ('sync', '=', False)]).unlink()

            view = self.env.ref('sh_message.sh_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            if s_missing:
                context['message'] = 'Cập nhật thành công! \n Các mã thuốc /vật tư sau chưa được khai báo trên phần mềm: %s ' % ",".join(s_missing)
            else:
                context['message'] = 'Cập nhật thành công!'
            return {
                'name': 'Success',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.message.wizard',
                'views': [(view_id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context,
            }
