from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime

def num2words_vnm(num):
    under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
                'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
    tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
    above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}

    if num < 20:
        return under_20[num]

    elif num < 100:
        under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
        result = tens[num // 10 - 2]
        if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
            result += ' ' + under_20[num % 10]
        return result

    else:
        unit = max([key for key in above_100.keys() if key <= num])
        result = num2words_vnm(num // unit) + ' ' + above_100[unit]
        if num % unit != 0:
            if num > 1000 and num % unit < unit / 10:
                result += ' không trăm'
            if 1 < num % unit < 10:
                result += ' linh'
            result += ' ' + num2words_vnm(num % unit)
    return result.capitalize()
class CRMButtonDebt(models.Model):
    _inherit = 'sh.medical.appointment.register.walkin'

    payment_debt = fields.Many2one('crm.debt.review', string='Phiếu duyệt nợ')
    paid = fields.Boolean('Đã trả nợ', default=False)

    def request_debt_review(self):
        total = 0
        for ser in self.service:
            total += ser.list_price

        return {
            'name': 'Yêu cầu duyệt nợ',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('shealth_all_in_one.debt_view_form').id,
            'res_model': 'crm.debt.review',
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit',
                'default_institution': self.institution.id,
                'default_walkin': self.id,
                'default_total': total,
                'default_patient': self.patient.id,
                'default_services': self.service.ids,
            },
        }

    def set_to_completed(self):
        res = super(CRMButtonDebt, self).set_to_completed()
        if self.payment_debt:
            if self.payment_debt.paid == False:
                raise ValidationError('Bạn cần tạo phiếu thanh toán để trả phiếu duyệt nợ trước khi đóng phiếu!')
        return res

    def request_debt_payment(self):
        service_name = ''
        total = 0
        for ser in self.service:
            total += ser.list_price
            service_name += ser.name + ";"
        new_record = self.env['account.payment'].create({
            'partner_id': self.patient.partner_id.id,
            'patient': self.patient.id,
            'company_id': self.patient.company_id.id,
            'currency_id': self.patient.currency_id.id,
            'amount': total,
            'note': "Thu tiền dịch vụ: " + service_name,
            'text_total': num2words_vnm(int(total)) + " đồng",
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'payment_date': datetime.date.today(),  # ngày thanh toán
            'date_requested': datetime.date.today(),  # ngày yêu cầu
            'payment_method_id': '1',
            'journal_id': 7,
            'walkin': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'res_id': new_record.id,
            'view_mode': 'form',
            'target': 'current',
        }
