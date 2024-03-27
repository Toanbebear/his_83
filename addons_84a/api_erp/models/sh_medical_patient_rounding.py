# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class ShMedicalPatientRounding(models.Model):
    _inherit = 'sh.medical.patient.rounding'

    def open_form_get_patient_rounding_erp(self):
        erp_url = self.env['ir.config_parameter'].sudo().get_param('api_erp.erp_url')
        if self.patient.phone:
            url = erp_url + '/api/83/v1/get-patient-rounding-ids/%s' % self.patient.phone
        else:
            raise ValidationError("Bệnh nhân chưa có số điện thoại!")
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        domain = []

        record_check = self.env['sh.medical.patient.rounding.test.erp'].sudo().search([('rounding_test_83', '=', self.id)])
        check_dict = []
        for rc in record_check:
            check_dict.append(rc.rounding_test_id)
            domain.append(rc.id)

        if 'data' in response and response['data']:
            for res in response['data']:
                # if 1 == 1:
                if res['rounding_test_id'] and int(res['rounding_test_id']) not in check_dict:
                    record = self.env['sh.medical.patient.rounding.test.erp'].sudo().create({
                        'rounding_test_83': self.id,
                        'walkin_id': res['walkin_id'],
                        'walkin_name': res['walkin_name'],
                        'rounding_test_id': res['rounding_test_id'],
                        'rounding_test_name': res['rounding_test_name'],
                    })
                    domain.append(record.id)
        view = {
            'name': 'Danh sách phiếu CSHP ERP',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('api_erp.view_sh_medical_patient_rounding_erp_tree').id,
            'res_model': 'sh.medical.patient.rounding.test.erp',
            'context': {},
            'domain': [('id', '=', domain)],
        }
        return view


class ShMedicalPatientRoundingTestERPFormLine(models.Model):
    _name = 'sh.medical.patient.rounding.test.erp'

    rounding_test_83 = fields.Many2one('sh.medical.patient.rounding', string='Phiếu 83')
    walkin_id = fields.Integer('ID phiếu khám')
    walkin_name = fields.Char('Mã phiếu khám erp')
    rounding_test_id = fields.Integer('ID phiếu CSHP erp')
    rounding_test_name = fields.Char('Mã phiếu CSHP erp')
    sync = fields.Boolean('Đã đồng bộ')
    payload = fields.Text('Payload')

    def sync_erp(self):
        erp_url = self.env['ir.config_parameter'].sudo().get_param('api_erp.erp_url')
        # url = "http://localhost:13000/api/83/v1/get-surgery/3092"
        if self.rounding_test_id:
            url = erp_url + "/api/83/v1/get-patient-rounding/%s" % str(self.rounding_test_id)
        else:
            raise ValidationError("Không lấy được ID ERP phiếu CSHP, liên hệ Admin để hỗ trợ!")
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
            self.rounding_test_83.sudo().sudo().write({
                'medicaments': [(5,)]
            })

            dict_sup_83 = dict((s['default_code'], s['id']) for s in supplies_83)
            line_sup_id = []
            for sup in data['supplies']:
                if sup['supply_code'] in dict_sup_83:
                    line_sup_id.append((0, 0, {
                        'medicine': dict_sup_83[sup['supply_code']],
                        'qty': int(sup['qty']),
                        'uom_id': self.env['sh.medical.medicines'].sudo().browse(int(dict_sup_83[sup['supply_code']])).uom_id.id if self.env['sh.medical.medicines'].sudo().browse(int(dict_sup_83[sup['supply_code']])) else False,
                        'location_id': self.rounding_test_83.inpatient_id.bed.room.location_medicine_stock.id if self.env['sh.medical.medicines'].sudo().browse(int(dict_sup_83[sup['supply_code']])).medicament_type == 'Medicine' else self.rounding_test_83.inpatient_id.bed.room.location_supply_stock.id,
                    }))

            # add lại vật tư theo data của erp
            # TODO cập nhật thêm trường nào thì viết vào đây
            self.rounding_test_83.sudo().write({
                'medicaments': line_sup_id,
                'evaluation_start_date': data['evaluation_start_date'],
                'evaluation_end_date': data['evaluation_end_date'],
            })

            self.sync = True
            self.payload = data
            # xóa bản ghi không dùng
            self.env['sh.medical.patient.rounding.test.erp'].sudo().search(
                [('rounding_test_83', '=', self.rounding_test_83.id), ('sync', '=', False)]).unlink()

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



