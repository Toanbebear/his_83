from odoo import models, api, fields, _
from odoo.exceptions import UserError
import requests
from odoo.exceptions import ValidationError


class ShMedicalPrescription(models.Model):
    _inherit = 'sh.medical.prescription'

    diagnose = fields.Text(string='Chẩn đoán(in trên đơn thuốc)')

    def open_form_get_prescription_erp(self):
        erp_url = self.env['ir.config_parameter'].sudo().get_param('api_erp.erp_url')
        if self.patient.phone:
            url = erp_url + '/api/83/v1/get-prescription-ids/%s' % self.patient.phone
            print(url)
        else:
            raise ValidationError("Bệnh nhân chưa có số điện thoại!")
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        domain = []

        record_check = self.env['sh.medical.prescription.erp'].sudo().search([('prescription_83', '=', self.id)])
        check_dict = []
        for rc in record_check:
            check_dict.append(rc.prescription_id)
            domain.append(rc.id)

        if 'data' in response and response['data']:
            for res in response['data']:
                if res['prescription_id'] and int(res['prescription_id']) not in check_dict:
                    record = self.env['sh.medical.prescription.erp'].sudo().create({
                        'prescription_83': self.id,
                        'walkin_id': res['walkin_id'],
                        'walkin_name': res['walkin_name'],
                        'prescription_id': res['prescription_id'],
                        'prescription_name': res['prescription_name'],
                        'service_patient_erp': res['service_patient_erp'],
                        'name_patient_erp': res['name_patient_erp'],
                        'prescription_date': res['prescription_date'],
                    })
                    domain.append(record.id)
        view = {
            'name': 'Danh sách ĐƠN THUỐC ERP',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('api_erp.view_sh_medical_prescription_erp_tree').id,
            'res_model': 'sh.medical.prescription.erp',
            'context': {},
            'domain': [('id', '=', domain)],
        }
        print(view)
        return view
class ShMedicalPrescriptionERP(models.Model):
    _name = 'sh.medical.prescription.erp'

    prescription_83 = fields.Many2one('sh.medical.prescription', string='Đơn thuốc 83')
    prescription_date = fields.Date('Ngày bệnh nhân làm dịch vụ')
    name_patient_erp = fields.Char('Tên bệnh nhân')
    service_patient_erp = fields.Char('Dịch vụ')
    walkin_id = fields.Integer('ID phiếu khám')
    walkin_name = fields.Char('Mã phiếu khám erp')
    prescription_id = fields.Integer('ID đơn thuốc')
    prescription_name = fields.Char('Mã đơn thuốc erp')
    sync = fields.Boolean('Đã đồng bộ')
    payload = fields.Text('Payload')

    def sync_erp(self):
        print('123')
        erp_url = self.env['ir.config_parameter'].sudo().get_param('api_erp.erp_url')
        # url = "http://localhost:13000/api/83/v1/get-surgery/3092"
        if self.prescription_id:
            url = erp_url + "/api/83/v1/get-prescription/%s" % str(self.prescription_id)
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
            self.prescription_83.sudo().sudo().write({
                'prescription_line': [(5,)]
            })

            dict_sup_83 = dict((s['default_code'], s['id']) for s in supplies_83)
            line_sup_id = []
            for sup in data['supplies']:
                if sup['supply_code'] in dict_sup_83:
                    line_sup_id.append((0, 0, {
                        'name': dict_sup_83[sup['supply_code']],
                        'qty': int(sup['qty_used']),
                        'info': sup['info'],
                        'dose_unit_related': self.env['sh.medical.medicines'].sudo().browse(int(dict_sup_83[sup['supply_code']])).uom_id.id if self.env['sh.medical.medicines'].sudo().browse(int(dict_sup_83[sup['supply_code']])) else False,
                    }))

            # add lại vật tư theo data của erp
            # TODO cập nhật thêm trường nào thì viết vào đây
            self.prescription_83.sudo().write({
                'prescription_line': line_sup_id,
                'date': data['date'],
                'date_out': data['date_out'],
                'diagnose': data['diagnose'],
            })

            self.sync = True
            self.payload = data
            # xóa bản ghi không dùng
            self.env['sh.medical.prescription.erp'].sudo().search(
                [('prescription_83', '=', self.prescription_83.id), ('sync', '=', False)]).unlink()

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
