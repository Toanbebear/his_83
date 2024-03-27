from odoo import api, fields, models, _

class SHealthServiceSpecialty(models.Model):
    _name = "sh.medical.service.specialty"

    name = fields.Char('Tên chuyên khoa')
    code = fields.Char('Mã chuyên khoa')





class InheritSHealthServices(models.Model):
    _inherit = "sh.medical.health.center.service"

    specialty_exam = fields.Many2one('sh.medical.service.specialty', 'Chuyên khoa')
    division_specialty = fields.Selection([
        ('I', 'Tuyến I'), ('II', 'Tuyến II'), ('III', 'Tuyến III'), ('IV', 'Tuyến IV'),
    ], 'Phân tuyến')
