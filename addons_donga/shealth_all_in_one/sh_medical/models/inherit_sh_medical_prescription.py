import logging
import pytz
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class InheritSHealthPrescriptionLines(models.Model):
    _inherit = 'sh.medical.prescription.line'
    _order = 'sequence'

    composition = fields.Char('Hoạt chất', compute='_get_composition')
    sequence = fields.Integer('Sequence', default=10)
    check_antibiotic = fields.Boolean('Là kháng sinh', default=False, compute='_get_composition', store=True)


    @api.depends('name')
    def _get_composition(self):
        for rec in self:
            # check hoạt chất
            if rec.name.composition:
                rec.composition = rec.name.composition
            else:
                rec.composition = 'Chưa có hoạt chất'

            # check là kháng sinh
            if rec.name.medicine_category_id.id == 208:
                rec.check_antibiotic = True
class InheritSHealthPrescription(models.Model):
    _inherit = 'sh.medical.prescription'

    duplicated_compositions = fields.Char(
        compute='_compute_duplicated_compositions',
        string='Duplicated Compositions',
        store=False)
#
    @api.depends('prescription_line.composition')
    def _compute_duplicated_compositions(self):
        for prescription in self:
            compositions = prescription.mapped('prescription_line.composition')
            composition_dict = {}
            for composition in compositions:
                line_ids = prescription.prescription_line.filtered(
                    lambda l: l.composition.strip() == composition.strip()).ids
                if composition in composition_dict:
                    composition_dict[composition].update(line_ids)
                else:
                    composition_dict[composition] = set(line_ids)
            duplicated_compositions = []
            for composition, line_ids in composition_dict.items():
                names = []
                if len(line_ids) > 1:
                    names = []
                    for line_id in line_ids:
                        name = prescription.prescription_line.filtered(
                            lambda l: l.id == line_id).name.default_code
                        names.append(name)
                    # duplicated_compositions.append(f"{', '.join(names)} có cùng hoạt chất {composition}, ")
                    duplicated_compositions.append(
                        "{names} có cùng hoạt chất {composition}, ".format(names=', '.join(names), composition=composition))
            if duplicated_compositions:
                prescription.duplicated_compositions = 'Cảnh báo:\n' + '\n'.join(duplicated_compositions)
            else:
                prescription.duplicated_compositions = False

    def action_prescription_out_stock(self):
        res = super(InheritSHealthPrescription, self).action_prescription_out_stock()
        if self.duplicated_compositions:
            raise ValidationError(_(self.duplicated_compositions + 'Bạn không thể xuất thuốc'))
        return res







