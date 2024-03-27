from odoo import api, fields, models, _

class SHealthInstitution(models.Model):
    _inherit = 'sh.medical.health.center'

    def get_domain_user(self):
        return [("groups_id", "in", [self.env.ref("shealth_all_in_one.group_sh_medical_accountant").id])]

    # người tạo phiếu thu
    user_payment = fields.Many2one('res.users', string='Người thu',
                           default=lambda self: self.env.ref("__import__.data_user_medical_thungan").id if self.env.ref(
                               "__import__.data_user_medical_thungan", False) else False,
                           domain=lambda self: self.get_domain_user())