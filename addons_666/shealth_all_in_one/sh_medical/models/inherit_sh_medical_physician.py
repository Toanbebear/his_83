from datetime import date
from odoo import fields, models, api


class InheritShMedicalPhysician(models.Model):
    _inherit = "sh.medical.physician"
    _description = "Thêm thông tin bác sĩ"

    so_cchn = fields.Char('Số CCHN')
    cc_qldd = fields.Boolean('CC QLĐD')
    cc_qlbv = fields.Boolean('CC QLBV')
    cc_ksnk_48t = fields.Boolean('CC KSNK (48 tiết)')
    cc_ksnk_3t = fields.Boolean('CC KSNK (3 tháng)')

    date_work = fields.Date('Ngày vào làm việc')
    type_quy = fields.Selection([
        ('Quý I', 'Quý I'), ('Quý II', 'Quý II'), ('Quý III', 'Quý III'), ('Quý IV', 'Quý IV')
    ], string="Quý")

    status = fields.Boolean('Đã nghỉ việc?', help='Nhân viên đã nghỉ việc thì tích là True')
