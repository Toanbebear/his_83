from odoo import fields, models, api
from odoo.exceptions import AccessError
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError,UserError
from datetime import date, datetime, time


class ShPrescriptionCancel(models.TransientModel):
    _name = 'sh.prescription.cancel'

    cancel = fields.Text(string='Lý do hủy', required=True)

    def set_cancel(self):
        pextend_id = self.env.context.get('active_id', False)
        pextend_record = self.env['sh.medical.prescription'].browse(pextend_id)
        pextend_record.update({
            'cancel': self.cancel,
            'state': 'cancel'
        })