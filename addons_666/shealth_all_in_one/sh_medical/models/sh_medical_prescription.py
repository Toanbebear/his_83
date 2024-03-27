from odoo import fields, models, api


class SHMedicalPrescriptions(models.Model):
    _inherit = 'sh.medical.prescription'
    _description = 'Thêm trạng thái hủy'

    STATES = [
        ('Draft', 'Draft'),
        # ('Invoiced', 'Invoiced'),
        # ('Sent to Pharmacy', 'Sent to Pharmacy'),
        ('Đã xuất thuốc', 'Đã xuất thuốc'),
        ('prescriptions', 'Thuốc kê đơn'),
        ('cancel', 'Đã hủy'),
    ]
    state = fields.Selection(STATES, 'State', readonly=True, default=lambda *a: 'Draft')
    cancel = fields.Text(string='Lý do hủy')
    diagnose = fields.Text(string='Chẩn đoán(in trên đơn thuốc)')

    def set_to_cancel(self):
        return {
            'name': 'Lý do hủy Toa Thuốc',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_prescription_cancel_form_view').id,
            'res_model': 'sh.prescription.cancel',
            'target': 'new',
            'context': {},
        }

    def action_prescription(self):
        self.state = 'prescriptions'

