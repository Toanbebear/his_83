import datetime
import time

from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError


class TrainingSchedule(models.Model):
    _name = 'training.schedule'
    _description = 'Lịch đào tạo nhân viên'

    start_date = fields.Datetime('Ngày bắt đầu', default=lambda self: fields.Datetime.now().replace(hour=1, minute=0, second=0))
    end_date = fields.Datetime('Ngày kết thúc')
    status = fields.Selection([
        ('1', 'Đã đào tạo'), ('2', 'Đang đào tạo'),
    ], string='Trạng thái', default='2')
    state = fields.Selection([
        ('1', 'Nháp'), ('2', 'Xác nhận'), ('3', 'Mở lại'), ('4', 'Hủy')
    ], string='Trạng thái', default='1')
    note = fields.Text('Ghi chú')
    training = fields.Char('Khóa đào tạo')
    number = fields.Char('Số tiết')
    employee = fields.Many2many('hr.employee', string='Tên nhân viên')
    department_id = fields.Many2one('sh.medical.health.center.ward', 'Làm việc tại khoa/phòng')
    partner_id = fields.Many2one('res.partner', 'Đơn vị tổ chức')

    # chuyển name
    def name_get(self):
        record = []
        for rec in self:
            if rec.employee:
                record.append((rec.id, "Lịch đào tạo" + " " + rec.department_id.name))
        return record

    @api.constrains('number')
    def check_phone(self):
        for rec in self:
            if rec.number:
                if rec.number.isdigit() is False:
                    raise ValidationError('Số tiết chỉ nhận giá trị số')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
                self.end_date = self.start_date.replace(hour=10, minute=30, second=0)

    # check ngày
    @api.constrains('end_date')
    def date_constrains(self):
        for rec in self:
            if rec.end_date and rec.start_date and rec.end_date <= rec.start_date:
                raise ValidationError('Ngày kết thúc không được lớn hơn ngày bắt đầu')

    def set_to_new(self):
        self.state = '2'

    def set_to_draft(self):
        self.state = '3'

    def set_to_cancel(self):
        self.state = '4'

    def unlink(self):
        for rec in self:
            if rec.state != "1":
                raise UserError('Bạn chỉ có thể xoá khi ở trạng thái nháp')
        return super(TrainingSchedule, self).unlink()