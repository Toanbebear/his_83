from odoo import fields, api, models, _

class InheritShMedicalPatient(models.Model):
    _inherit = 'sh.medical.patient'

    district_id = fields.Many2one('res.country.district', string='Quận/huyện', domain="[('state_id','=', state_id)]")
    ward_id = fields.Many2one('res.country.ward', string='Phường/xã', domain="[('district_id','=', district_id)]")

    @api.onchange('district_id')
    def onchange_district_id(self):
        self.ward_id = False

    @api.onchange('state_id')
    def onchange_state_id(self):
        self.district_id = False
        self.ward_id = False