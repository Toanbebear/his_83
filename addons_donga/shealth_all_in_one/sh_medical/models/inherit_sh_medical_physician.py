from odoo import fields, models, api


class InheritShMedicalPhysician(models.Model):
    _inherit = "sh.medical.physician"
    _description = "Them thông tin bác sĩ"

    so_cchn = fields.Char('Số CCHN')
    cc_qldd = fields.Boolean('CC QLĐD')
    cc_qlbv = fields.Boolean('CC QLBV')
    cc_ksnk_48t = fields.Boolean('CC KSNK (48 tiết)')
    cc_ksnk_3t = fields.Boolean('CC KSNK (3 tháng)')

