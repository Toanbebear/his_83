from odoo import fields, api, models, _

class ShMedicalPatient(models.Model):
    _inherit = 'sh.medical.patient'

    weight = fields.Float(string='Chiều cao (kg)')
    height = fields.Float(string='Cân nặng (cm)')
    bmi = fields.Float(string='Chỉ số khối cơ thể (BMI)', compute="compute_bmi")

    @api.onchange('height', 'weight')
    def onchange_height_weight(self):
        res = {}
        if self.height:
            self.bmi = self.weight / ((self.height / 100) ** 2)
        else:
            self.bmi = 0
        return res

    def compute_bmi(self):
        for rec in self:
            if rec.height and rec.weight:
                rec.bmi = rec.weight / ((rec.height / 100) ** 2)
