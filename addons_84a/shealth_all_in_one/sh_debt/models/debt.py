from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class DebtReview(models.Model):
    _name = 'crm.debt.review'
    _description = 'Duyệt nợ'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Text('Lý do nợ', tracking=True)
    stage = fields.Selection([('offer', 'Đề xuất'), ('approve', 'Duyệt'), ('refuse', 'Từ chối')], string='Trạng thái',
                             default='offer', tracking=True)
    institution = fields.Many2one('sh.medical.health.center',string='Cơ sở y tế',default=lambda self: self.env.ref('shealth_all_in_one.sh_medicines_health_center_kangnam_hn').id,)
    patient = fields.Many2one('sh.medical.patient', string='Đối tác', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Đơn vị tiền tệ', related='services.currency_id')
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Phiếu khám')
    services = fields.Many2many('sh.medical.health.center.service',  string='dịch vụ')
    total = fields.Monetary('Tổng tiền phải thu')
    amount_owed = fields.Monetary('Số tiền nợ', tracking=True)
    paid = fields.Boolean('Đã trả nợ', tracking=True)
    user_approve = fields.Many2one('res.users', 'Người duyệt nợ', tracking=True)
    date_approve = fields.Datetime('Ngày duyêt', tracking=True)
    paid = fields.Boolean('Đã trả nợ', tracking=True)

    @api.onchange('patient')
    def onchange_patient(self):
        if self.patient:
            return {'domain': {'walkin': [
                ('id', 'in', self.env['sh.medical.appointment.register.walkin'].search(
                    [('patient', '=', self.patient.id)]).ids)]}}

    @api.onchange('walkin')
    def onchange_services(self):
        if self.services:
            return {'domain': {'walkin': [
                ('id', 'in', self.env['sh.medical.appointment.register.walkin'].search(
                    [('service', 'in', self.services.ids)]).ids)]}}

    def action_paid(self):
        self.paid = True
        # self.order_id.amount_owed -= self.amount_owed
        self.color = 0

    def set_approve(self):
        for rec in self:
            if rec.amount_owed == rec.total:
                rec.stage = 'approve'
                rec.walkin.set_to_progress()
                rec.date_approve = fields.Datetime.now()
                rec.user_approve = self.env.user.id
                rec.walkin.payment_debt = self.id
            else:
                raise ValidationError('Bạn cần nhập đủ số tiền cần thu mới có thể xác nhận!')

    def unlink(self):
        if self.stage == 'approve':
            raise ValidationError('Bạn chỉ có thể xóa khi ở trọng thái nháp!')
        elif self.stage == 'refuse':
            raise ValidationError('Bạn chỉ có thể hủy phiếu chứ k thể xóa!')

    def set_refuse(self):
        if self.stage == 'approve':
            raise ValidationError('Khi phiếu đã được duyệt, chỉ Quản lý mới có quyền hủy phiếu!')
        elif self.stage == 'refuse':
            raise ValidationError('Phiếu này đã ở trạng thái hủy rồi!')
        else:
            self.stage = 'refuse'