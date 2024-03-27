from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, time
from calendar import monthrange
from openpyxl import load_workbook
from openpyxl.styles import Font, borders, Alignment
import base64
from io import BytesIO
from dateutil.relativedelta import relativedelta
from pytz import timezone, utc
from num2words import num2words

import logging

thin = borders.Side(style='thin')
double = borders.Side(style='double')
all_border_thin = borders.Border(thin, thin, thin, thin)

class ToolUpdateAccountPayment(models.TransientModel):
    _name = 'tool.update.account.payment'
    _description = 'Thêm tool cập nhật phiếu thanh toán'

    payment_id = fields.Many2one('account.payment', string='Phiếu thu', help='Thông tin phiếu thu')
    payment_walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')
    payment_patient = fields.Many2one('sh.medical.patient', string='Bệnh nhân')
    payment_note = fields.Text('Lý do thu')
    payment_text_total = fields.Text('Số tiền bằng chữ')
    payment_amount = fields.Monetary('Tổng thanh toán')
    payment_user = fields.Many2one('res.users', string='Người thu')
    payment_date = fields.Date(string='Ngày thanh toán', required=True)
    journal_id = fields.Many2one('account.journal', string='Hình thức thanh toán')
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)

    @api.onchange('payment_amount')
    def onchange_payment_amount(self):
        if self.payment_amount and self.payment_amount > 0:
            if self.currency_id == self.env.ref('base.VND'):
                self.payment_text_total = num2words(round(self.payment_amount), lang='vi_VN') + " đồng"
                self.payment_text_total = self.payment_text_total.title()
        else:
            self.payment_text_total = "Không đồng"

    def update_payment(self):
        for rec in self:
            self.payment_id.write({
                'amount': self.payment_amount,
                'text_total': self.payment_text_total,
                'payment_date': self.payment_date,
                'note': self.payment_note,
                'user': self.payment_user.id,
                'currency_id': self.currency_id.id,
            })





