from odoo import models, fields


class PhysicianCalendar(models.Model):
    _inherit = "sh.medical.physician"

    is_resign = fields.Boolean('Đã nghỉ việc?')