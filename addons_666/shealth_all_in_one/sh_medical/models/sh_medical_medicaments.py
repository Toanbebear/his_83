##############################################################################
#    Copyright (C) 2018 shealth (<http://scigroup.com.vn/>). All Rights Reserved
#    shealth, Hospital Management Solutions

# Odoo Proprietary License v1.0
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, shealth.in, openerpestore.com, or if you have received a written
# agreement from the authors of the Software.
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

##############################################################################

from odoo import api, fields, models, _
from odoo.osv import expression
from lxml import etree
from odoo.osv.orm import setup_modifiers

class SHealthProductTemplate(models.Model):
    _inherit = "product.template"

    _sql_constraints = [
        ('unique_product_default_code', 'unique (default_code)', 'Mã nội bộ phải là duy nhất!')
    ]

# Medicines
class SHealthMedicines(models.Model):
    _name = 'sh.medical.medicines'
    _description = "Information about the medicines"
    _inherits={
        'product.product': 'product_id',
    }

    _order = "name_use ASC"

    MEDICAMENT_TYPE = [
        ('Medicine', 'Medicine'),
        ('Supplies', 'Supplies'),
        # ('Vaccine', 'Vaccine'),
    ]

    product_id = fields.Many2one('product.product', string='Related Product', required=True, ondelete='cascade', help='Product-related data of the medicines')

    name_use = fields.Char(string='Tên sử dụng', size=128, help="Tên sử dụng")
    name_medicine = fields.Char(string='Tên biệt dược', size=128, help="Tên biệt dược để báo cáo")
    index_medicine = fields.Char(string='STT biệt dược', size=128, help="Số thứ tự trong báo cáo thuốc. vd: 1.2")
    atc_code = fields.Char(string='Mã ATC', size=128, help="Mã chuẩn ATC để báo cáo")
    composition_index = fields.Char(string='STT hoạt chất', size=128, help="STT hoạt chất để báo cáo")

    therapeutic_action = fields.Char(string='Therapeutic effect', size=128, help="Therapeutic action")
    composition = fields.Text(string='Composition', help="Components")
    # indications = fields.Text(string='Đường dùng',help="Đường dùng")
    indications = fields.Many2one('sh.medical.drug.route', string="Đường dùng", help="Đường dùng của thuốc")
    dosage = fields.Text(string='Liều dùng', help="Liều dùng")
    overdosage = fields.Text(string='Overdosage',help="Overdosage")
    pregnancy_warning = fields.Boolean(string='Pregnancy Warning', help="Check when the drug can not be taken during pregnancy or lactancy")
    pregnancy = fields.Text(string='Pregnancy and Lactancy',help="Warnings for Pregnant Women")
    adverse_reaction = fields.Text(string='Adverse Reactions')
    storage = fields.Text(string='Storage Conditions')
    info = fields.Text(string='Extra Info')
    medicament_type = fields.Selection(MEDICAMENT_TYPE, string='Medicament Type')
    origin = fields.Many2one('sh.foreign', string='Nước sản xuất', ondelete='restrict')
    production_company = fields.Char(string='Hãng sản xuất', size=128)
    registration_code = fields.Char(string='Số đăng ký', size=128)
    concentration = fields.Text(string='Nồng độ/Hàm lượng')

    # code = fields.Char(string='Code', help='Code of medicine')

    medicine_category_id = fields.Many2one('sh.medical.medicines.category', string='Medicines category', help='Category of the medicines')

    # Thông tin đơn thuốc quốc gia
    code_national = fields.Char(string='Mã dược quốc gia')
    national_prescription = fields.Boolean(string='Đơn thuốc quốc gia?', default=False)
    name_prescription = fields.Char('Tên thuốc theo đơn thuốc', compute="_compute_name_prescription")
    # name_prescription = fields.Char('Tên thuốc theo đơn thuốc')

    @api.depends('composition')
    def _compute_name_prescription(self):
        for record in self:
            if record.composition and '+' in record.composition:
                # record.name_prescription = f"{record.name_medicine or record.name} {record.concentration}"
                record.name_prescription = "%s %s" % (record.name_medicine or record.name, record.concentration)
            else:
                # record.name_prescription = (f"{record.composition}({record.name_medicine or record.name}) {record.concentration}")
                record.name_prescription = "%s(%s) %s" % (record.composition, record.name_medicine or record.name, record.concentration)

    @api.model
    def create(self, vals):
        # sp luôn là loại lưu dc kho
        vals['type'] = 'product'
        # nếu là thuốc thì sẽ tracking by lot
        if vals.get('medicament_type') == 'Medicine':
            vals['tracking'] = 'lot'
        return super(SHealthMedicines, self).create(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SHealthMedicines, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                             submenu=submenu)

        doc = etree.XML(res['arch'])

        if self.env.context.get('default_medicament_type', True) == "Medicine":
            for node in doc.xpath("//field[@name='medicine_category_id']"):
                node.set('domain', "[('type', '=', 'Medicine')]")
                setup_modifiers(node, res['fields']['medicine_category_id'])
        else:
            for node in doc.xpath("//field[@name='composition']"):
                node.set('string', 'Thành phần')

            for node in doc.xpath("//field[@name='medicine_category_id']"):
                node.set('domain', "[('type', '=', 'Supplies')]")
                setup_modifiers(node, res['fields']['medicine_category_id'])

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.multi
    def name_get(self):
        res = []
        for medicines in self:
            if medicines.medicament_type == 'Medicine':
                res.append((medicines.id, _('[%s] %s %s %s ') % (medicines.default_code, medicines.name_use[0:50], medicines.composition or '', medicines.concentration or '')))
            else:
                res.append((medicines.id, _('[%s] %s %s') % (medicines.default_code, medicines.name_use[0:50], medicines.origin.name or '')))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|', '|', ('name', operator, name), ('default_code', operator, name),
                      ('name_use', operator, name), ('name_medicine', operator, name), ('composition', operator, name)]
        medicament = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(medicament).name_get()

    @api.onchange('medicament_type')
    def _onchange_institution(self):
        if self.medicament_type == 'Medicine':
            self.categ_id = self.env.ref('shealth_all_in_one.sh_medicines').id
        else:
            self.categ_id = self.env.ref('shealth_all_in_one.sh_supplies').id

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        if self.uom_id:
            self.uom_po_id = self.uom_id

    def action_open_quants(self):
        products = self.mapped('product_variant_ids')
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        action['context'] = {'search_default_internal_loc': 1}
        return action

    def action_view_stock_move_lines(self):
        self.ensure_one()
        action = self.env.ref('stock.stock_move_line_action').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action

    def action_open_product_lot(self):
        self.ensure_one()
        action = self.env.ref('stock.action_production_lot_form').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', '=', self.id)]
        if self.product_variant_count == 1:
            action['context'] = {
                'default_product_id': self.product_variant_id.id,
            }

        return action

    def action_view_orderpoints(self):
        products = self.mapped('product_variant_ids')
        action = self.env.ref('stock.product_open_orderpoint').read()[0]
        if products and len(products) == 1:
            action['context'] = {'default_product_id': products.ids[0], 'search_default_product_id': products.ids[0]}
        else:
            action['domain'] = [('product_id', 'in', products.ids)]
            action['context'] = {}
        return action

# Medicaments Configuration
class SHealthDoseUnit(models.Model):
    _name = "sh.medical.dose.unit"
    _description = "Medical Dose Unit"
    name = fields.Char(string='Unit', size=32, required=True)
    desc = fields.Char(string='Description', size=64)

class SHealthDrugRoute(models.Model):
    _name = "sh.medical.drug.route"
    _description = "Medical Drug Route"
    name = fields.Char(string='Route', size=32, required=True)
    code = fields.Char(string='Code', size=64)

class SHealthDrugForm(models.Model):
    _name = "sh.medical.drug.form"
    _description = "Medical Dose Form"
    name = fields.Char(string='Form', size=32, required=True)
    code = fields.Char(string='Code', size=64)

class SHealthDosage (models.Model):
    _name = "sh.medical.dosage"
    _description = "Medicines Dosage"
    name = fields.Char(string='Frequency', size=256, help='Common dosage frequency')
    code = fields.Char(string='Code', size=64, help='Dosage Code, such as SNOMED, 229798009 = 3 times per day')
    abbreviation = fields.Char(string='Abbreviation', size=64, help='Dosage abbreviation, such as tid in the US or tds in the UK')


class SHealthMedicineCategory (models.Model):
    _name = "sh.medical.medicines.category"
    _description = "Medicines Category"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    type = fields.Selection([('Medicine', 'Thuốc'),('Supplies', 'Vật tư')], required=True, string='Loại nhóm', default='Medicine')
