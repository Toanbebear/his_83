import datetime
import time

from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError


class EmSchedule(models.Model):
    _name = 'em.schedule'
    _description = 'lịch làm việc nhân viên'

    start_date = fields.Datetime('Ngày bắt đầu', default=lambda self: fields.Datetime.now().replace(hour=1, minute=0, second=0))
    end_date = fields.Datetime('Ngày kết thúc')
    status = fields.Selection([
        ('1', 'Nghỉ phép'), ('2', 'Đi làm'), ('3', 'Nghỉ dài hạn'), ('4', 'làm theo ca'), ('5', 'Nghỉ đi học'), ('6', 'Nghỉ đi công tác'),
        ('7', 'Ra trực'), ('8', 'Nghỉ lễ'), ('9', 'Nghỉ thai sản'), ('10', 'Nghỉ không lương'), ('11', 'Nghỉ ốm, con ốm'), ('12', 'Trực đêm')
    ], string='Trạng thái làm việc', default='2')
    state = fields.Selection([
        ('1', 'Nháp'), ('2', 'Xác nhận'), ('3', 'Mở lại'), ('4', 'Hủy')
    ], string='Trạng thái', default='1')
    note = fields.Text('Lý do')
    employee = fields.Many2many('hr.employee', string='Tên nhân viên')
    department_id = fields.Many2one('sh.medical.health.center.ward', 'Làm việc tại khoa/phòng')

    # chuyển name
    def name_get(self):
        record = []
        for rec in self:
            if rec.employee:
                record.append((rec.id, "Lịch làm việc tại" + " " + rec.department_id.name))
        return record

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
        return super(EmSchedule, self).unlink()