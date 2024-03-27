from odoo import api, SUPERUSER_ID, fields, models, _
from odoo.osv import expression

class SHealthPathologyICD9(models.Model):
    _name = 'sh.medical.pathology.icd9'
    _description = 'Danh mục ICD9'

    name = fields.Char(string='Tên ICD-9', size=128, help="Disease name", translate=True, required=True)
    code = fields.Char(string='Mã ICD-9', size=32, help="Mã cụ thể cho bệnh (eg, ICD-10, SNOMED...)")

    @api.multi
    def name_get(self):
        res = []
        for category in self:
            res.append((category.id, _('[%s] %s') % (category.code, category.name[0:50])))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        pathology = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(pathology).name_get()