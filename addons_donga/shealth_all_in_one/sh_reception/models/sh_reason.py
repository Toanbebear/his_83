from odoo import api, fields, models, _

class SHReason(models.Model):
    _name = 'sh.reason'
    _description = 'Đón tiếp'

    name = fields.Char('Lý do khám')
    service_room_id = fields.Many2many('sh.medical.health.center.ot', string='Phòng khám', domain=lambda self: [('department', '=', self.env.ref('shealth_all_in_one.sh_kb_dep_knhn').id)])