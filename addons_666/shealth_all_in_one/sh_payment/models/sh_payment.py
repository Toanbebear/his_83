##############################################################################
#    Copyright (C) 2018 shealth (<http://scigroup.com.vn/>). All Rights Reserved
#    shealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, shealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo.tools.float_utils import float_round, float_compare


# Inherit Payment

class SHealthAccountPayment(models.Model):
    _inherit = 'account.payment'

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')
    patient = fields.Many2one('sh.medical.patient', string='Bệnh nhân')
    note = fields.Text('Lý do thu')
    text_total = fields.Text('Số tiền bằng chữ')
    date_requested = fields.Datetime(string='Ngày giờ yêu cầu', help="Ngày giờ yêu cầu", readonly=False,
                                     states={'posted': [('readonly', True)], 'cancelled': [('readonly', True)]},
                                     default=lambda *a: datetime.datetime.now())
    
    service_room = fields.Many2one('sh.medical.health.center.ot', related='walkin.service_room', store=True)
    
    def get_domain_user(self):
        return [("groups_id", "in", [self.env.ref("shealth_all_in_one.group_sh_medical_accountant").id])]

    # người tạo phiếu
    user = fields.Many2one('res.users', string='Người thu',
                           default=lambda self: self.env.ref("__import__.data_user_medical_thungan").id if self.env.ref(
                               "__import__.data_user_medical_thungan", False) else False,
           domain=lambda self: self.get_domain_user())

    # nội dung giao dịch
    @api.onchange('communication')
    def get_communication(self):
        if self.walkin:
            self.communication = self.note

    # XÁC NHẬN THANH TOÁN
    @api.multi
    def post(self):
        for payment in self:
            if payment.walkin.payment_debt:
                payment.walkin.payment_debt.write({
                    'paid': True
                })
                payment.walkin.paid = True
            else:
                payment.walkin.set_to_progress()
        return super(SHealthAccountPayment, self).post()

    @api.multi
    def unlink(self):#xóa phiếu thu sẽ hiện lại yêu cầu thu phí
        for payment in self:
            payment.walkin.write({'state': 'Scheduled'})
        return super(SHealthAccountPayment, self).unlink()
    def tool_update_payment(self):
        return {
            'name': 'Cập nhật phiếu thu',
            'view_mode': 'form',
            'res_model': 'tool.update.account.payment',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('shealth_all_in_one.tool_update_account_payment_form').id,
            'context': {
                'default_payment_id': self.id,
                'default_payment_walkin': self.walkin.id,
                'default_payment_patient': self.patient.id,
                'default_payment_note': self.note,
                'default_payment_amount': self.amount,
                'default_payment_text_total': self.text_total,
                'default_payment_user': self.user.id,
                'default_payment_date': self.payment_date,
                'default_journal_id': self.journal_id.id,
                'default_currency_id': self.currency_id.id,
            },
            'target': 'new'
        }
