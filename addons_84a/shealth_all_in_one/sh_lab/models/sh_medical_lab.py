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
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
import time
import datetime
from odoo.tools import float_is_zero, float_compare, pycompat

class SHealthLabGroupType(models.Model):
    _name = 'sh.medical.lab.group.type'
    _description = 'Lab Group Type Configuration'

    name = fields.Char(string='Name', size=128, required=True)
    info = fields.Text(string='Description')


# Lab Units Management

class SHealthLabTestUnits(models.Model):
    _name = 'sh.medical.lab.units'
    _description = 'Lab Test Units'

    name = fields.Char(string='Unit Name', size=25, required=True)
    code = fields.Char(string='Code', size=25, required=True)

    _sql_constraints = [('name_uniq', 'unique(name)', 'The Lab unit name must be unique')]


# Lab Test Department
# class shealthLabTestDepartment(models.Model):
#     _name = 'sh.medical.labtest.department'
#     _description = 'Lab Test Departments'
#
#     name = fields.Char(string='Name', size=128, required=True)

# Lab Test Types Management

class SHealthLabTestCriteria(models.Model):
    _name = 'sh.medical.labtest.criteria'
    _description = 'Lab Test Criteria'

    name = fields.Char(string='Tests', size=128, required=True)
    normal_range = fields.Text(string='Normal Range')
    abnormal = fields.Boolean(string='Abnormal', default=False)
    units = fields.Many2one('sh.medical.lab.units', string='Units')
    sequence = fields.Integer(string='Sequence')
    medical_type_id = fields.Many2one('sh.medical.labtest.types', string='Lab Test Types')

    _order = "sequence"


class SHealthLabTestTypes(models.Model):
    _name = 'sh.medical.labtest.types'
    _description = 'Lab Test Types'

    _inherits = {
        'product.product': 'product_id',
    }

    product_id = fields.Many2one('product.product', string='Related Product', required=True, ondelete='cascade',
                                 help='Product-related data of the labtest types')

    # name = fields.Char(string='Lab Test Name', required=True, help="Test type, eg X-Ray, Hemogram, Biopsy...")
    # default_code = fields.Char(help="Short code for the test")

    info = fields.Text(string='Description')
    lab_criteria = fields.One2many('sh.medical.labtest.criteria', 'medical_type_id', string='Lab Test Cases')
    # lab_department = fields.Many2one('sh.medical.labtest.department', string='Department')

    # institution = fields.Many2one('sh.medical.health.center', string='Health Center', help="Medical Center")
    # department = fields.Many2one('sh.medical.health.center.ward', string='Department', help="Department of the selected Health Center", domain="[('institution','=',institution)]")
    # thong tin vat tu
    material_ids = fields.One2many('sh.medical.labtest.types.material', 'labtest_types_id',
                                   string="Material Information")

    has_child = fields.Boolean(string='Có xét nghiệm con', default=False)
    normal_range = fields.Text(string='Khoảng bình thường')

    # gruop_type
    group_type = fields.Many2one('sh.medical.lab.group.type', string='Group',
                                 help="Group of the imaging test type")

    machine_name = fields.Text(string='Tên máy')


class SHealthLabTestTypesMaterial(models.Model):
    _name = 'sh.medical.labtest.types.material'
    _description = 'All material of the Lab Test Types'

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự
    labtest_types_id = fields.Many2one('sh.medical.labtest.types', string='Lab Test Types')
    product_id = fields.Many2one('sh.medical.medicines', string='Product', required=True, domain=lambda self: [
        ('categ_id', 'child_of', self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    quantity = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'))  # số lượng sử dụng vật tư
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')

    @api.onchange('product_id')
    def _change_product_id(self):
        self.uom_id = self.product_id.uom_id

        return {'domain': {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.product_id.uom_id.category_id:
            self.uom_id = self.product_id.uom_id
            raise Warning(
                _('The Lab Test Types Unit of Measure and the Material Unit of Measure must be in the same category.'))


class SHealthLabTests(models.Model):
    _name = 'sh.medical.lab.test'
    _description = 'Lab Tests'

    _inherit = [
        'mail.thread']

    _order = "name"

    LABTEST_STATE = [
        ('Draft', 'Draft'),
        ('Test In Progress', 'Test In Progress'),
        ('Completed', 'Completed'),
        # ('Cancelled', 'Cancelled'),
        # ('Invoiced', 'Invoiced'),
    ]

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự

    name = fields.Char(string='Lab Test #', size=16, readonly=True, required=True, help="Lab result ID",
                       default=lambda *a: '/')
    # lab_department = fields.Many2one('sh.medical.labtest.department', string='Department', readonly=True, states={'Draft': [('readonly', False)]})
    test_type = fields.Many2one('sh.medical.labtest.types', string='Test Type', required=True, readonly=True,
                                states={'Draft': [('readonly', False)]}, help="Lab test type")
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True,
                              states={'Draft': [('readonly', False)]})
    pathologist = fields.Many2one('sh.medical.physician', string='Pathologist', help="Pathologist", readonly=True,
                                  states={'Draft': [('readonly', False)]})
    requestor = fields.Many2one('sh.medical.physician', string='Doctor who requested the test',
                                help="Doctor who requested the test", readonly=True,
                                states={'Draft': [('readonly', False)]})
    results = fields.Text(string='Results', readonly=True,
                          states={'Draft': [('readonly', False)], 'Test In Progress': [('readonly', False)]})
    diagnosis = fields.Text(string='Diagnosis', readonly=True,
                            states={'Draft': [('readonly', False)], 'Test In Progress': [('readonly', False)]})
    lab_test_criteria = fields.One2many('sh.medical.lab.resultcriteria', 'medical_lab_test_id',
                                        string='Lab Test Result', readonly=True, states={'Draft': [('readonly', False)],
                                                                                         'Test In Progress': [
                                                                                             ('readonly', False)]})
    date_requested = fields.Datetime(string='Date requested', readonly=True,
                                     states={'Draft': [('readonly', False)], 'Test In Progress': [('readonly', False)]},
                                     default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    date_analysis = fields.Datetime(string='Date of the Analysis', readonly=True,
                                    states={'Draft': [('readonly', False)], 'Test In Progress': [('readonly', False)]})
    date_done = fields.Datetime(string='Date of the return result', readonly=True,
                                states={'Draft': [('readonly', False)], 'Test In Progress': [('readonly', False)]})
    state = fields.Selection(LABTEST_STATE, string='State', readonly=True, default=lambda *a: 'Draft')

    # benh vien
    institution = fields.Many2one('sh.medical.health.center', string='Health Center', help="Medical Center")
    department = fields.Many2one('sh.medical.health.center.ward', string='Department',
                                 help="Department of the selected Health Center",
                                 domain="[('institution','=',institution),('type','=','Laboratory')]")

    perform_room = fields.Many2one('sh.medical.health.center.ot', string='Performance room',
                                   domain="[('department','=',department)]", readonly=True,
                                   states={'Draft': [('readonly', False)]})
    # thong tin vat tu
    lab_test_material_ids = fields.One2many('sh.medical.lab.test.material', 'lab_test_id',
                                            string="Material Information", readonly=True,
                                            states={'Draft': [('readonly', False)],
                                                    'Test In Progress': [('readonly', False)]})

    has_child = fields.Boolean(string='Có xét nghiệm con', default=False)
    normal_range = fields.Text(string='Khoảng bình thường')
    abnormal = fields.Boolean(string='Bất thường', default=False, compute="_compute_results")

    @api.onchange('date_requested', 'date_analysis', 'date_done')
    def _onchange_date_labtest(self):
        if self.date_analysis and self.date_requested and self.date_done:
            if self.date_analysis < self.date_requested or self.date_analysis > self.date_done:
                raise UserError(
                    _('Thông tin không hợp lệ! Ngày phân tích phải sau ngày yêu cầu và trước ngày trả kết quả!'))

    @api.multi
    def write(self, vals):
        if vals.get('date_requested') or vals.get('date_analysis') or vals.get('date_done'):
            for record in self:
                date_requested = vals.get('date_requested') or record.date_requested
                date_analysis = vals.get('date_analysis') or record.date_analysis
                date_done = vals.get('date_done') or record.date_done

                # format to date
                if isinstance(date_requested, pycompat.string_types):
                    date_requested = datetime.datetime.strptime(date_requested, '%Y-%m-%d %H:%M:%S')
                if isinstance(date_analysis, pycompat.string_types):
                    date_analysis = datetime.datetime.strptime(date_analysis, '%Y-%m-%d %H:%M:%S')
                if isinstance(date_done, pycompat.string_types):
                    date_done = datetime.datetime.strptime(date_done, '%Y-%m-%d %H:%M:%S')

                if date_analysis and date_requested and date_done and (date_analysis < date_requested or date_analysis > date_done):
                    raise UserError(
                        _('Thông tin không hợp lệ! Ngày phân tích phải sau ngày yêu cầu và trước ngày trả kết quả!'))

        return super(SHealthLabTests, self).write(vals)

    @api.multi
    def view_detail_labtest(self):
        return {
            'name': _('Chi tiết xét nghiệm'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_lab_test_form').id,
            'res_model': 'sh.medical.lab.test',  # model want to display
            'target': 'new',  # if you want popup,
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': self.id
        }

    @api.depends('results', 'lab_test_criteria')
    def _compute_results(self):
        for labtest in self:
            if not labtest.has_child:  # ko co xet nghiem con
                if labtest.results:
                    if labtest.normal_range:  # co set khoang binh thuong
                        r = labtest.results
                        nr = labtest.normal_range.replace('(', '').replace(')', '')
                        # dang gia tri nam trong khoang
                        if "-" in nr:
                            if r.replace('.', '', 1).isdigit():
                                r = eval(labtest.results)
                                nr_list = nr.split('-')
                                if r < eval(nr_list[0]) or r > eval(nr_list[1]):
                                    labtest.abnormal = True
                            else:
                                labtest.abnormal = True
                                # raise UserError(_('The value entered is not valid!'))
                        elif "<" in nr or ">" in nr:
                            if r.replace('.', '', 1).isdigit():
                                # r = eval(self.result)
                                if not eval(r + nr):
                                    labtest.abnormal = True
                            else:
                                labtest.abnormal = True
                                # raise UserError(_('The value entered is not valid!'))
                        else:
                            if r.lower() == nr.lower():
                                labtest.abnormal = False
                            else:
                                labtest.abnormal = True
            else:
                if labtest.lab_test_criteria:
                    labtest.abnormal = True if len(
                        labtest.lab_test_criteria.filtered(lambda case: case.abnormal)) > 0 else False

    @api.depends('test_type')
    def compute_test_type(self):
        for record in self:
            record.group_type = record.test_type.group_type if record.test_type else False

    # gruop_type
    group_type = fields.Many2one('sh.medical.lab.group.type', string='Group', store="1",
                                 help="Group of the imaging test type", compute=compute_test_type)

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.lab.test')
        vals['name'] = sequence or '/'
        res = super(SHealthLabTests, self).create(vals)

        # chưa có case thì tạo
        if not res.lab_test_criteria:
            data_case = res.onchange_test_type_id_values(res.test_type.id)['value']['lab_test_criteria']
            d = [(0, 0, i) for i in data_case]
            res.write({'lab_test_criteria': d})

        return res

    @api.onchange('institution')
    def _onchange_institution(self):
        # set khoa mac dinh la khoa xet nghiem cua co so y te
        if self.institution:
            lab_dep = self.env['sh.medical.health.center.ward'].search(
                [('institution', '=', self.institution.id), ('type', '=', 'Laboratory')], limit=1)
            self.department = lab_dep

    # @api.onchange('department')
    # def _onchange_department(self):
    #     if not self.institution:
    #         self.institution = self.department.institution.id
    #     self.test_type = ''

    # Fetching lab test types
    @api.onchange('test_type')
    def onchange_test_type_id(self):
        self.lab_test_criteria = ''
        self.lab_test_material_ids = ''
        self.results = ''
        self.abnormal = False
        self.has_child = self.test_type.has_child if self.test_type else False
        self.normal_range = self.test_type.normal_range if self.test_type else False
        self.perform_room = False if self.env.ref('shealth_all_in_one.sh_labtest_room_knhn',
                                                  False) == None else self.env.ref(
            'shealth_all_in_one.sh_labtest_room_knhn').id
        self.department = self.perform_room.department if self.perform_room else False

        values = self.onchange_test_type_id_values(self.test_type.id if self.test_type else False)
        return values

    @api.multi
    def onchange_test_type_id_values(self, test_type):
        ### set value for test case lab test by type ###
        criteria_obj = self.env['sh.medical.labtest.criteria']
        labtest_ids = []

        res = {}

        # if no test type present then nothing will process
        if (not test_type):
            return res

        # defaults
        res = {'value': {
            'lab_test_criteria': [],
            'lab_test_material_ids': []
        }
        }

        # Getting lab test lines values
        query = _(
            "select name, sequence, normal_range, abnormal, units from sh_medical_labtest_criteria where medical_type_id=%s") % (
                    str(test_type))
        self.env.cr.execute(query)
        vals = self.env.cr.fetchall()
        if vals:
            for va in vals:
                specs = {
                    'name': va[0],
                    'sequence': va[1],
                    'normal_range': va[2],
                    'abnormal': va[3],
                    'units': va[4],
                }
                labtest_ids += [specs]

        ### set value for material lab test by type ###
        material_obj = self.env['sh.medical.lab.test.material']
        material_ids = []

        # Getting lab test lines mats values
        query_material = _(
            "select  sequence, product_id, quantity , uom_id from sh_medical_labtest_types_material where labtest_types_id=%s") % (
                             str(test_type))
        self.env.cr.execute(query_material)
        vals_material = self.env.cr.fetchall()
        if vals_material:
            for va_ma in vals_material:
                specs_ma = {
                    'sequence': va_ma[0],
                    'product_id': va_ma[1],
                    'init_quantity': va_ma[2],
                    'quantity': va_ma[2],
                    'is_init': True,
                    'uom_id': va_ma[3],
                }
                material_ids += [specs_ma]

        res['value'].update({
            'lab_test_criteria': labtest_ids,
            'lab_test_material_ids': material_ids,
        })
        return res

    # This function prints the lab test
    @api.multi
    def print_patient_labtest(self):
        return self.env.ref('shealth_all_in_one.action_report_patient_labtest').report_action(self)

    @api.multi
    def set_to_test_inprogress(self):
        print('Labtesst: Test In Progress')
        if self.state == 'Completed':
            self.reverse_materials()
            res = self.write({'state': 'Test In Progress'})
        else:
            # ghi nhận case xn và vtth mẫu từ test type
            # self.lab_test_material_ids = False
            # self.lab_test_criteria = False
            # if self.test_type:
            #     lt_data = []
            #     test_type_id = self.test_type.id
            #     test_type = self.env['sh.medical.labtest.types'].sudo().browse(test_type_id)
            #     seq = 0
            #     for lt in test_type.material_ids:
            #         seq += 1
            #         lt_data.append((0, 0, {'sequence': seq,
            #                                'product_id': lt.product_id.id,
            #                                'init_quantity': lt.quantity,
            #                                'is_init': True,
            #                                'uom_id': lt.uom_id.id}))
            #
            #     lt_case_data = []
            #     test_type = self.env['sh.medical.labtest.types'].sudo().browse(test_type_id)
            #     seq_case = 0
            #     for lt_case in test_type.lab_criteria:
            #         seq_case += 1
            #         lt_case_data.append((0, 0, {'sequence': seq_case,
            #                                     'name': lt_case.name,
            #                                     'normal_range': lt_case.normal_range,
            #                                     'units': lt_case.units.id}))

            # log access patient
            data_log = self.env['sh.medical.patient.log'].search([('walkin', '=', self.walkin.id)])
            data_xn = False
            for data in data_log:
                # nếu đã có data log cho khoa xn này rồi
                if data.department.id == self.department.id:
                    data_xn = data
                # nếu có log khoa KB rồi thì cập nhật ngày ra cho khoa kb là ngày bắt đầu XN
                if data.department.type == 'Examination' and not data.date_out:
                    data.date_out = self.date_analysis if self.date_analysis else datetime.datetime.now()
            # nếu chưa có data log=> tạo log
            if not data_xn:
                vals_log = {'walkin': self.walkin.id,
                            'patient': self.patient.id,
                            'department': self.department.id,
                            'date_in': self.date_analysis if self.date_analysis else datetime.datetime.now()}
                self.env['sh.medical.patient.log'].create(vals_log)
            else:
                data_xn.date_in = self.date_analysis if self.date_analysis else datetime.datetime.now()
                data_xn.date_out = False

            res = self.write({'state': 'Test In Progress',
                              'date_analysis': self.date_analysis if self.date_analysis else datetime.datetime.now()})

        # res = self.write({'state': 'Test In Progress', 'date_analysis': datetime.datetime.now()})
        # update so phieu hoan thanh
        Walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.walkin.id)
        lt_done = self.env['sh.medical.lab.test'].search_count(
            [('walkin', '=', self.walkin.id), ('state', '=', 'Completed')])
        lt_total = self.env['sh.medical.lab.test'].search_count(
            [('walkin', '=', self.walkin.id), ('state', '!=', 'Cancelled')])

        Walkin.write({'lab_test_done_count': lt_done, 'has_lab_result': True if lt_total - lt_done == 0 else False})
        return res

    @api.multi
    def set_to_test_draft(self):
        print('Labtesst: Draft')
        res = self.write({'state': 'Draft', 'date_analysis': False})
        return res

    def reverse_materials(self):
        key_words = 'THBN - %s - %s' % (self.name, self.walkin.name)
        pick_need_reverse = self.env['stock.picking'].search([('origin', 'ilike', key_words)], order='create_date DESC',
                                                             limit=1)
        fail_pick_count = self.env['stock.picking'].search_count([('name', 'ilike', pick_need_reverse.name)])
        if pick_need_reverse.id:
            date_done = pick_need_reverse.date_done

            pick_need_reverse.name += '-FP%s' % fail_pick_count
            pick_need_reverse.move_ids_without_package.write(
                {'reference': pick_need_reverse.name})  # sửa cả trường tham chiếu của move.line (Dịch chuyển kho)
            wizard = self.env['stock.return.picking'].with_context(active_id=pick_need_reverse.id, reopen_flag=True,
                                                                   no_check_quant=True).create(
                {'picking_id': pick_need_reverse.id})
            new_picking_id, pick_type_id = wizard._create_returns()
            new_picking = self.env['stock.picking'].browse(new_picking_id)
            new_picking.with_context(exact_location=True).action_assign()
            for move_line in new_picking.move_ids_without_package:
                for move_live_detail in move_line.move_line_ids:
                    move_live_detail.qty_done = move_live_detail.product_uom_qty
                # move_line.quantity_done = move_line.product_uom_qty
            new_picking.button_validate()

            # sua ngay hoan thanh
            for move_line in new_picking.move_ids_without_package:
                move_line.move_line_ids.write(
                    {'date': date_done})  # sửa ngày hoàn thành ở stock move line
            new_picking.move_ids_without_package.write(
                {'date': date_done})  # sửa ngày hoàn thành ở stock move

            new_picking.date_done = date_done
            new_picking.sci_date_done = date_done

    @api.multi
    def set_to_test_complete(self):
        print('Labtesst: Completed')
        # tru vat tu theo tieu hao của phiếu xét nghiệm
        # if self.evaluation_type == 'Inpatient Admission':  # nếu loại đánh giá là nhập viện thì trừ vật tư ở khoa hậu phẫu
        #     dept = self.env['sh.medical.health.center.ward'].search(
        #         [('institution', '=', self.walkin.institution.id), ('type', '=', 'Inpatient')], limit=1)
        # else:  # nếu là loại đánh giá khác thì trừ vtth ở khoa theo phiếu khám
        #     dept = self.env['sh.medical.health.center.ward'].search([('id', '=', self.walkin.department.id)], limit=1)
        if self.has_child:
            if len(self.lab_test_criteria.filtered(lambda case: not case.result)) > 0:
                raise UserError(_('Bạn không thể xác nhận phiếu hoàn thành khi chưa nhập đầy đủ kết quả.'))
        else:
            if not self.results:
                raise UserError(_('Bạn không thể xác nhận phiếu hoàn thành khi chưa nhập đầy đủ kết quả.'))

        dept = self.department
        room = self.perform_room
        if self.date_done:
            date_done = self.date_done
        else:
            date_done = fields.Datetime.now()

        vals = []
        validate_str = ''
        for mat in self.lab_test_material_ids:
            if mat.quantity > 0:  # CHECK SO LUONG SU DUNG > 0
                quantity_on_hand = self.env['stock.quant']._get_available_quantity(mat.product_id.product_id,
                                                                                   room.location_supply_stock)  # check quantity trong location
                if mat.uom_id != mat.product_id.uom_id:
                    mat.write({'quantity': mat.uom_id._compute_quantity(mat.quantity, mat.product_id.uom_id),
                               'uom_id': mat.product_id.uom_id.id})  # quy so suong su dung ve don vi chinh cua san pham

                if quantity_on_hand < mat.quantity:
                    validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
                        mat.product_id.default_code, mat.product_id.name, str(quantity_on_hand), str(mat.uom_id.name),
                        room.location_supply_stock.name)
                else:  # truong one2many trong stock picking de tru cac product trong inventory
                    vals.append((0, 0, {
                        'name': 'THBN: ' + mat.product_id.product_id.name,
                        'origin': str(self.walkin.id) + "-" + str(self.walkin.service.ids),  # mã pk-mã dịch vụ
                        'date': date_done,
                        'company_id': self.env.user.company_id.id,
                        'date_expected': date_done,
                        'date_done': date_done,
                        'product_id': mat.product_id.product_id.id,
                        'product_uom_qty': mat.quantity,
                        'product_uom': mat.uom_id.id,
                        'location_id': room.location_supply_stock.id,
                        'location_dest_id': self.patient.partner_id.property_stock_customer.id,
                        'partner_id': self.patient.partner_id.id,
                        # xuat cho khach hang/benh nhan nao
                    }))

        # neu co vat tu tieu hao
        if vals and validate_str == '':
            # tao phieu xuat kho
            # picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
            #                                                       ('warehouse_id', '=',
            #                                                        self.walkin.institution.warehouse_ids[0].id)],
            #                                                      limit=1).id
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
                                                                  ('warehouse_id', '=',
                                                                   self.env.ref('stock.warehouse0').id)],
                                                                 limit=1).id
            pick_note = 'THBN - %s - %s' % (self.name, self.walkin.name)
            pick_vals = {'note': pick_note,
                         'origin': pick_note,
                         'partner_id': self.patient.partner_id.id,
                         'patient_id': self.patient.id,
                         'picking_type_id': picking_type,
                         'location_id': room.location_supply_stock.id,
                         'location_dest_id': self.patient.partner_id.property_stock_customer.id,
                         'date_done': date_done,
                         # xuat cho khach hang/benh nhan nao
                         'immediate_transfer': True,
                         'move_ids_without_package': vals}
            fail_pick_name = self.env['stock.picking'].search(
                [('origin', 'ilike', 'THBN - %s - %s' % (self.name, self.walkin.name))], limit=1).name
            if fail_pick_name:
                pick_vals['name'] = fail_pick_name.split('-', 1)[0]
            stock_picking = self.env['stock.picking'].create(pick_vals)
            # KO TU DONG XUAT KHO NUA MA CHI TAO PHIEU XUAT THOI
            stock_picking.with_context(exact_location=True).action_assign()  # ham check available trong inventory
            for move_line in stock_picking.move_ids_without_package:
                for move_live_detail in move_line.move_line_ids:
                    move_live_detail.qty_done = move_live_detail.product_uom_qty
                # move_line.quantity_done = move_line.product_uom_qty
            stock_picking.button_validate()  # ham tru product trong inventory

            # sua ngay hoan thanh
            for move_line in stock_picking.move_ids_without_package:
                move_line.move_line_ids.write({'date': date_done})  # sửa ngày hoàn thành ở stock move line
            stock_picking.move_ids_without_package.write(
                {'date': date_done})  # sửa ngày hoàn thành ở stock move
            stock_picking.date_done = date_done
            stock_picking.sci_date_done = date_done

            stock_picking.create_date = self.date_analysis

        elif validate_str != '':
            raise ValidationError(_(
                "Các loại Vật tư sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))

        # log access patient
        data_log = self.env['sh.medical.patient.log'].search([('walkin', '=', self.walkin.id)])
        data_xn = False
        for data in data_log:
            # nếu đã có data log cho khoa xn này rồi
            if data.department.id == self.department.id:
                data_xn = data
            # nếu có log khoa KB rồi thì cập nhật ngày ra cho khoa kb là ngày bắt đầu làm dịch vụ
            # if data.department.type == 'Examination':
            #     data.date_out = self.services_date
        # nếu chưa có data log=> tạo log
        if not data_xn:
            vals_log = {'walkin': self.walkin.id,
                        'patient': self.patient.id,
                        'department': self.department.id,
                        'date_in': self.date_analysis if self.date_analysis else datetime.datetime.now()}
            self.env['sh.medical.patient.log'].create(vals_log)
        else:
            data_xn.date_in = self.date_analysis if self.date_analysis else datetime.datetime.now()
            data_xn.date_out = self.date_done if self.date_done else datetime.datetime.now()

        # cap nhat trang thai
        res = self.write({'state': 'Completed', 'date_done': date_done})

        # cap nhat vat tu cho phieu kham - ẩn do chưa dùng
        self.walkin.update_walkin_material()

        # update so phieu hoan thanh
        Walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.walkin.id)
        lt_done = self.env['sh.medical.lab.test'].search_count(
            [('walkin', '=', self.walkin.id), ('state', '=', 'Completed')])
        lt_total = self.env['sh.medical.lab.test'].search_count(
            [('walkin', '=', self.walkin.id), ('state', '!=', 'Cancelled')])

        Walkin.write({'lab_test_done_count': lt_done, 'has_lab_result': True if lt_total - lt_done == 0 else False})

        return res

    # @api.multi
    # def set_to_test_cancelled(self):
    #     return self.write({'state': 'Cancelled'})

    @api.multi
    def unlink(self):
        for labtest in self.filtered(lambda labtest: labtest.state not in ['Draft']):
            raise UserError(_('You can not delete a lab test which is not in "Draft" state !!'))
        return super(SHealthLabTests, self).unlink()

    @api.multi
    def _default_account(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.default_credit_account_id.id

    # def action_lab_invoice_create(self):
    #     invoice_obj = self.env["account.invoice"]
    #     invoice_line_obj = self.env["account.invoice.line"]
    #
    #     for lab in self:
    #         # Create Invoice
    #         if lab.patient:
    #             curr_invoice = {
    #                 'partner_id': lab.patient.partner_id.id,
    #                 'account_id': lab.patient.partner_id.property_account_receivable_id.id,
    #                 'state': 'draft',
    #                 'type':'out_invoice',
    #                 'date_invoice': datetime.date.today(),
    #                 'origin': "Lab Test# : " + lab.name,
    #                 'target': 'new',
    #             }
    #
    #             inv_ids = invoice_obj.create(curr_invoice)
    #             inv_id = inv_ids.id
    #
    #             if inv_ids:
    #                 prd_account_id = self._default_account()
    #                 if lab.test_type:
    #
    #                     # Create Invoice line
    #                     curr_invoice_line = {
    #                         'name': "Charge for " + str(lab.test_type.name) + " laboratory test",
    #                         'price_unit': lab.test_type.test_charge or 0,
    #                         'quantity': 1.0,
    #                         'account_id': prd_account_id,
    #                         'invoice_id': inv_id,
    #                     }
    #
    #                     inv_line_ids = invoice_line_obj.create(curr_invoice_line)
    #
    #             self.write({'state': 'Invoiced'})
    #
    #     return {
    #             'domain': "[('id','=', " + str(inv_id) + ")]",
    #             'name': 'Lab Test Invoice',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             'res_model': 'account.invoice',
    #             'type': 'ir.actions.act_window'
    #     }


class SHealthLabTestMaterial(models.Model):
    _name = 'sh.medical.lab.test.material'
    _description = 'All material of the Lab Test'

    _order = "product_id ASC"

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự
    lab_test_id = fields.Many2one('sh.medical.lab.test', string='Lab Test')
    product_id = fields.Many2one('sh.medical.medicines', string='Tên', required=True,
                                 domain=lambda self: [('categ_id', 'child_of',
                                                       self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
                             compute='compute_available_qty_supply')
    init_quantity = fields.Float('Initial Quantity',
                                 digits=dp.get_precision('Product Unit of Measure'),
                                 readonly=True)  # số lượng bom ban đầu của vật tư
    quantity = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'))  # số lượng sử dụng vật tư

    is_init = fields.Boolean('Is Initial', default=False)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')

    _order = "sequence"

    @api.depends('product_id')
    def compute_available_qty_supply(self):
        for record in self:
            record.qty_avail = record.product_id.qty_available if record.product_id else 0

    @api.onchange('product_id')
    def _change_product_id(self):
        self.uom_id = self.product_id.uom_id

        return {'domain': {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.product_id.uom_id.category_id:
            self.uom_id = self.product_id.uom_id
            raise Warning(
                _('The Lab Test Unit of Measure and the Material Unit of Measure must be in the same category.'))


class SHealthLabTestsResultCriteria(models.Model):
    _name = 'sh.medical.lab.resultcriteria'
    _description = 'Lab Test Result Criteria'

    name = fields.Char(string='Tests', size=128, required=True)
    result = fields.Text(string='Result')
    normal_range = fields.Text(string='Normal Range')
    abnormal = fields.Boolean(string='Abnormal', default=False, compute="_compute_result")
    units = fields.Many2one('sh.medical.lab.units', string='Units')
    sequence = fields.Integer(string='Sequence')
    medical_lab_test_id = fields.Many2one('sh.medical.lab.test', string='Lab Tests')

    _order = "sequence"

    @api.depends('result')
    def _compute_result(self):
        for record in self:
            if record.result:
                if record.normal_range:
                    r = record.result
                    nr = record.normal_range.replace('(', '').replace(')', '')
                    # dang gia tri nam trong khoang
                    if "-" in nr:
                        if r.replace('.', '', 1).isdigit():
                            r = eval(record.result)
                            nr_list = nr.split('-')
                            if nr_list[0].replace('.', '', 1).isdigit() and nr_list[1].replace('.', '', 1).isdigit():
                                if r < eval(nr_list[0]) or r > eval(nr_list[1]):
                                    record.abnormal = True
                        else:
                            pass
                            # raise UserError(_('Giá trị nhập cho xét nghiệm %s không hợp lệ!' % record.name))
                            # raise UserError(_('The value entered is not valid!'))
                    elif "<" in nr or ">" in nr:
                        if r.replace('.', '', 1).isdigit():
                            # r = eval(self.result)
                            if not eval(r + nr):
                                record.abnormal = True
                                record.medical_lab_test_id.abnormal = True
                        else:
                            raise UserError(_('Giá trị nhập cho xét nghiệm %s không hợp lệ!' % record.name))
                            # raise UserError(_('The value entered is not valid!'))
                    else:
                        if r.lower() == nr.lower():
                            record.abnormal = False
                        else:
                            record.abnormal = True


# Inheriting Patient module to add "Lab" screen reference
class SHealthPatient(models.Model):
    _inherit = 'sh.medical.patient'

    @api.multi
    def _labtest_count(self):
        oe_labs = self.env['sh.medical.lab.test']
        for ls in self:
            domain = [('patient', '=', ls.id)]
            lab_ids = oe_labs.search(domain)
            labs = oe_labs.browse(lab_ids)
            labs_count = 0
            for lab in labs:
                labs_count += 1
            ls.labs_count = labs_count
        return True

    lab_test_ids = fields.One2many('sh.medical.lab.test', 'patient', string='Lab Tests')
    labs_count = fields.Integer(compute=_labtest_count, string="Lab Tests")


# Inheriting Ward module to add "LabTest" screen reference
class SHealthWard(models.Model):
    _inherit = 'sh.medical.health.center.ward'

    labtest = fields.One2many('sh.medical.lab.test', 'department', string='LabTest')
    count_lab_not_completed = fields.Integer('Labtest not completed', compute="_count_lab_not_completed")

    @api.multi
    def _count_lab_not_completed(self):
        oe_labs = self.env['sh.medical.lab.test']
        for ls in self:
            domain = [('state', '!=', 'Completed'), ('department', '=', ls.id)]
            ls.count_lab_not_completed = oe_labs.search_count(domain)
        return True