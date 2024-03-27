# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import requests

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class ShMedicalLabTest(models.Model):
    _inherit = 'sh.medical.lab.test'

    def open_form_get_lab_test_erp(self):
        erp_url = self.env['ir.config_parameter'].sudo().get_param('api_erp.erp_url')
        # url = "http://localhost:13000/api/83/v1/get-lab-test-ids/0935958899"
        if self.patient.phone:
            url = erp_url + '/api/83/v1/get-lab-test-ids/%s' % self.patient.phone
        else:
            raise ValidationError("Bệnh nhân chưa có số điện thoại!")
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        domain = []

        record_check = self.env['sh.medical.lab.test.erp'].sudo().search([('lab_test_83', '=', self.id)])
        check_dict = []
        for rc in record_check:
            check_dict.append(rc.lab_test_id)
            domain.append(rc.id)

        if 'data' in response and response['data']:
            for res in response['data']:
                # if 1 == 1:
                if res['lab_test_id'] and int(res['lab_test_id']) not in check_dict:
                    record = self.env['sh.medical.lab.test.erp'].sudo().create({
                        'lab_test_83': self.id,
                        'walkin_id': res['walkin_id'],
                        'walkin_name': res['walkin_name'],
                        'lab_test_id': res['lab_test_id'],
                        'lab_test_name': res['lab_test_name'],
                    })
                    domain.append(record.id)
        view = {
            'name': 'Danh sách phiếu xét nghiệm ERP',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('api_erp.view_sh_medical_lab_test_erp_tree').id,
            'res_model': 'sh.medical.lab.test.erp',
            'context': {},
            'domain': [('id', '=', domain)],
        }
        return view


class ShMedicalLabTestERPFormLine(models.Model):
    _name = 'sh.medical.lab.test.erp'

    lab_test_83 = fields.Many2one('sh.medical.lab.test', string='Phiếu 83')
    walkin_id = fields.Integer('ID phiếu khám')
    walkin_name = fields.Char('Mã phiếu khám')
    lab_test_id = fields.Integer('ID phiếu xét nghiệm')
    lab_test_name = fields.Char('Mã phiếu xét nghiệm')
    sync = fields.Boolean('Đã đồng bộ')
    payload = fields.Text('Payload')

    def sync_erp(self):
        erp_url = self.env['ir.config_parameter'].sudo().get_param('api_erp.erp_url')
        # url = "http://localhost:13000/api/83/v1/get-lab-test/233551"
        if self.lab_test_id:
            url = erp_url + "/api/83/v1/get-lab-test/%s" % str(self.lab_test_id)
        else:
            raise ValidationError("Không lấy được ID ERP phiếu xét nghiệm, liên hệ Admin để hỗ trợ!")
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        if 'data' in response and response['data']:
            data = response['data']
            # check mã vật tư
            supplies_erp = data['materials_code']
            supplies_83 = self.env['sh.medical.medicines'].sudo().search([('default_code', 'in', supplies_erp)])
            s83 = [x.default_code for x in supplies_83]

            # check vật tư bị thiếu
            s_missing = [x for x in supplies_erp if x not in s83]

            # bỏ toàn bộ vật tư & kết quả
            self.lab_test_83.sudo().sudo().write({
                'lab_test_material_ids': [(5,)]
            })
            # line vật tư
            uom_ids = self.env['uom.uom'].sudo().search([])
            dict_uom = {}
            for uom_id in uom_ids:
                dict_uom[uom_id.name.lower()] = uom_id.id
            dict_sup_83 = dict((s['default_code'], s['id']) for s in supplies_83)
            line_sup_id = []
            for sup in data['materials']:
                if sup['product_code'] in dict_sup_83:
                    line_sup_id.append((0, 0, {
                        'product_id': dict_sup_83[sup['product_code']],
                        'quantity': int(sup['quantity']),
                        'uom_id': dict_uom[sup['uom_id'].lower()] if sup['uom_id'].lower() in dict_uom else False,
                    }))

            # check phiếu có xét nghiệm con không
            if self.lab_test_83.has_child:
                self.lab_test_83.sudo().sudo().write({
                    'lab_test_criteria': [(5,)]
                })
                # tạo line
                lab_test_criteria = []
                for ltc in data['lab_test_cases']:
                    unit = self.env['sh.medical.lab.units'].sudo().search([('name', '=', ltc['units'])], limit=1)
                    lab_test_criteria.append((0, 0, {
                        'name': ltc['name'],
                        'result': ltc['result'],
                        'normal_range': ltc['normal_range'],
                        'abnormal': ltc['abnormal'],
                        'units': unit.id if unit else False,
                    }))
                print(len(lab_test_criteria))
                # add lại vật tư theo data của erp
                # TODO cập nhật thêm trường nào thì viết vào đây
                self.lab_test_83.sudo().write({
                        'lab_test_material_ids': line_sup_id,
                        'lab_test_criteria': lab_test_criteria
                    })
            else:
                # TODO cập nhật thêm trường nào thì viết vào đây
                self.lab_test_83.sudo().write({
                    'lab_test_material_ids': line_sup_id,
                    'results': data['results']
                })

            self.sync = True
            self.payload = data
            # xóa bản ghi không dùng
            self.env['sh.medical.lab.test.erp'].sudo().search(
                [('lab_test_83', '=', self.lab_test_83.id), ('sync', '=', False)]).unlink()

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



