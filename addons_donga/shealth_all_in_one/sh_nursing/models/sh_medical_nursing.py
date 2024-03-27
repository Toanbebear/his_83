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

from odoo import fields, api, models, _
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
from odoo.addons import decimal_precision as dp
import datetime

# Patient Roundings Management

class SHealthPatientRoundingProcedures(models.Model):
    _name = 'sh.medical.patient.rounding.procedure'
    _description = 'Patient Procedures For Roundings'

    name = fields.Many2one('sh.medical.patient.rounding', string='Rouding')
    procedures = fields.Many2one('sh.medical.procedure', string='Procedures', required=True)
    notes = fields.Text('Notes')


class SHealthPatientRoundingMedicines(models.Model):
    _name = 'sh.medical.patient.rounding.medicines'
    _description = 'Patient Medicines For Roundings'

    _order = "medicine ASC"

    MEDICAMENT_TYPE = [
        ('Medicine', 'Medicine'),
        ('Supplies', 'Supplies'),
    ]

    name = fields.Many2one('sh.medical.patient.rounding', string='Rounding')
    # medicine = fields.Many2one('sh.medical.medicines', string='Medicines and Supply', domain=lambda self:[('categ_id','child_of',self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)], required=True)
    medicine = fields.Many2one('sh.medical.medicines', string='Medicines and Supply', required=True)
    # medicine = fields.Many2one('sh.medical.medicines', string='Medicines', domain=[('medicament_type','=','Medicine')], required=True)
    qty_avail = fields.Float(string='Số lượng khả dụng', required=True, help="Số lượng khả dụng trong toàn viện",
                             compute='compute_available_qty_supply')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    qty = fields.Float("Quantity", digits=dp.get_precision('Product Unit of Measure'),default=lambda *a: 1)
    notes = fields.Text('Comment')

    location_id = fields.Many2one('stock.location', 'Stock location', domain="[('usage', '=', 'internal')]")
    medicament_type = fields.Selection(MEDICAMENT_TYPE, related="medicine.medicament_type", string='Medicament Type',
                                       store=True)

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự

    @api.depends('medicine')
    def compute_available_qty_supply(self):
        for record in self:
            record.qty_avail = record.medicine.qty_available if record.medicine else 0

    @api.onchange('qty', 'medicine')
    def onchange_qty(self):
        if self.qty <= 0 and self.medicine:
            raise UserError(_("Số lượng nhập phải lớn hơn 0!"))

    @api.onchange('medicine')
    def _change_product_id(self):
        self.uom_id = self.medicine.uom_id
        if self.medicament_type == 'Medicine':
            self.location_id = self.name.inpatient_id.bed.room.location_medicine_stock.id
        else:
            self.location_id = self.name.inpatient_id.bed.room.location_supply_stock.id


class SHealthPatientRoundingManagement(models.Model):
    _name = 'sh.medical.patient.rounding'
    _description = 'Patient Rounding Management'

    _order = "name"

    STATUS = [
        ('Draft', 'Draft'),
        ('Completed', 'Completed'),
    ]

    EVOLUTION = [
        ('Status Quo', 'Status Quo'),
        ('Improving', 'Improving'),
        ('Worsening', 'Worsening'),
    ]

    @api.multi
    def _get_patient_rounding(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    def get_nurse(self):
        if self.env.ref('__import__.khn_medical_job_dd',False):
            return [('is_pharmacist', '=', False), ('job_id', '=', self.env.ref('__import__.khn_medical_job_dd').id)]
        else:
            return [('is_pharmacist', '=', False)]

    def get_anesthetist(self):
        if self.env.ref('__import__.khn_medical_job_gmhs',False):
            return [('is_pharmacist', '=', False), ('job_id', '=', self.env.ref('__import__.khn_medical_job_gmhs').id)]
        else:
            return [('is_pharmacist', '=', False)]

    def _get_default_medicines(self):
        # nếu có tồn tại context chứa dịch vụ đã thực hiện
        if self.env.context.get('services_done') and self.env.context.get('room'):
            services = self.env.context.get('services_done')

            service_materials = self.env['sh.medical.service.material']
            inpatient_room = self.env['sh.medical.health.center.ot']

            domain = [('service_id', 'in', services[0][2]),('note','=','Inpatient')]
            service_materials_data = service_materials.search(domain)
            inpatient_room_data = inpatient_room.browse(self.env.context.get('room'))

            # ghi nhận vtth nếu có
            materials_rounding = []
            seq = 0

            id_product_material_rounding = []
            for material in service_materials_data:
                #nếu ko có sẽ add thêm vtth đó vào, ko thì bỏ qua
                if material.product_id.id not in id_product_material_rounding:
                    seq += 1

                    if material.product_id.medicament_type == 'Medicine':
                        location_id = inpatient_room_data.location_medicine_stock.id
                    else:
                        location_id = inpatient_room_data.location_supply_stock.id

                    materials_rounding.append((0, 0, {'sequence': seq,
                                           'medicament_type': material.product_id.medicament_type,
                                           'location_id': location_id or False,
                                           'medicine': material.product_id.id,
                                           'qty': material.quantity,
                                           'note': '',
                                           'uom_id': material.uom_id.id}))

                    id_product_material_rounding.append(material.product_id.id)  #co roi se khong add thêm nữa

            return materials_rounding
        else:
            return False

    name = fields.Char(string='Rounding #', size=128, readonly=True, default=lambda *a: '/')
    inpatient_id = fields.Many2one('sh.medical.inpatient', string='Registration Code', required=True, readonly=True, states={'Draft': [('readonly', False)]})
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True, states={'Draft': [('readonly', False)]})
    doctor = fields.Many2one('sh.medical.physician', domain=lambda self: self.get_anesthetist(), string='Bác sĩ', help="Physician Name", required=True, readonly=True,states={'Draft': [('readonly', False)]}, default=_get_patient_rounding)
    physician = fields.Many2one('sh.medical.physician', domain=lambda self: self.get_nurse(), string='Điều dưỡng viên', help="Physician Name", required=True, readonly=True,states={'Draft': [('readonly', False)]}, default=_get_patient_rounding)
    evaluation_start_date = fields.Datetime(string='Start date & time', required=True, readonly=True, states={'Draft': [('readonly', False)]}, default=lambda *a: datetime.datetime.now())
    evaluation_end_date = fields.Datetime(string='End date & time', readonly=True, states={'Draft': [('readonly', False)]})
    temperature = fields.Float(string='Temperature', help="Temperature in celsius", readonly=True,
                               states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.temperature", store=True)
    bpm = fields.Integer(string='Heart Rate', help="Heart rate expressed in beats per minute", readonly=True,
                         states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.bpm", store=True)
    respiratory_rate = fields.Integer(string='Respiratory Rate',
                                      help="Respiratory rate expressed in breaths per minute", readonly=True,
                                      states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.respiratory_rate", store=True)
    systolic = fields.Integer(string='Systolic Pressure', readonly=True, states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.systolic", store=True)
    diastolic = fields.Integer(string='Diastolic Pressure', readonly=True, states={'Draft': [('readonly', False)]}, related="inpatient_id.walkin.diastolic", store=True)
    osat = fields.Integer(string='Oxygen Saturation', help="Oxygen Saturation(arterial)", readonly=True,
                          states={'Draft': [('readonly', False)]})

    # NOT USE
    environmental_assessment = fields.Char('Environment', help="Environment assessment. State any disorder in the room.", size=128, readonly=True, states={'Draft': [('readonly', False)]})
    weight = fields.Integer(string='Weight', help="Measured weight, in kg", readonly=True, states={'Draft': [('readonly', False)]})
    pain = fields.Boolean(string='Pain', help="Check if the patient is in pain", readonly=True, states={'Draft': [('readonly', False)]})
    pain_level = fields.Integer(string='Pain Level (1 to 10)', help="Enter the pain level, from 1 to 10", readonly=True, states={'Draft': [('readonly', False)]})
    potty = fields.Boolean(string='Potty', help="Check if the patient needs to urinate / defecate", readonly=True, states={'Draft': [('readonly', False)]})
    position = fields.Boolean(string='Position', help="Check if the patient needs to be repositioned or is unconfortable", readonly=True, states={'Draft': [('readonly', False)]})
    proximity = fields.Boolean(string='Proximity', help="Check if personal items, water, alarm, ... are not in easy reach", readonly=True, states={'Draft': [('readonly', False)]})
    pump = fields.Boolean(string='Pumps', help="Check if personal items, water, alarm, ... are not in easy reach", readonly=True, states={'Draft': [('readonly', False)]})
    personal_needs = fields.Boolean(string='Personal needs', help="Check if the patient requests anything", readonly=True, states={'Draft': [('readonly', False)]})
    diuresis = fields.Integer(string='Diuresis', help="volume in ml", readonly=True, states={'Draft': [('readonly', False)]})
    urinary_catheter = fields.Integer(string='Urinary Catheter', readonly=True, states={'Draft': [('readonly', False)]})
    glycemia = fields.Integer(string='Glycemia', help="Blood Glucose level", readonly=True, states={'Draft': [('readonly', False)]})
    depression = fields.Boolean(string='Depression Signs', help="Check this if the patient shows signs of depression", readonly=True, states={'Draft': [('readonly', False)]})
    # NOT USE

    evolution = fields.Selection(EVOLUTION, string='Evolution', readonly=True, states={'Draft': [('readonly', False)]})
    round_summary = fields.Text(string="Round Summary", readonly=True, states={'Draft': [('readonly', False)]})
    execute = fields.Html(string="Thực hiện y lệnh", readonly=True, states={'Draft': [('readonly', False)]})
    warning = fields.Boolean(string='Warning', help="Check this box to alert the supervisor about this patient rounding. A warning icon will be shown in the rounding list", readonly=True, states={'Draft': [('readonly', False)]})
    procedures = fields.One2many('sh.medical.patient.rounding.procedure', 'name', string='Procedures', help="List of the procedures in this rounding. Please enter the first one as the main procedure", readonly=True, states={'Draft': [('readonly', False)]})
    medicaments = fields.One2many('sh.medical.patient.rounding.medicines', 'name', default=lambda self: self._get_default_medicines(), string='Medicines', help="List of the medicines assigned in this rounding", readonly=True, states={'Draft': [('readonly', False)]})
    state = fields.Selection(STATUS, string='State',readonly=True, default=lambda *a: 'Draft')

    @api.onchange('evaluation_start_date')
    def _onchange_date(self):
        # if not self.evaluation_end_date:
        self.evaluation_end_date = self.evaluation_start_date

    @api.multi
    # Preventing deletion of a rounding details which is not in draft state
    def unlink(self):
        for nursing in self.filtered(lambda nursing: nursing.state not in ['Draft']):
            raise UserError(_('You can not delete rounding information which is not in "Draft" state !!'))
        return super(SHealthPatientRoundingManagement, self).unlink()

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.patient.rounding')
        vals['name'] = sequence
        return super(SHealthPatientRoundingManagement, self).create(vals)

    def reverse_materials(self):
        num_of_location = len(self.medicaments.mapped('location_id'))
        pick_need_reverses = self.env['stock.picking'].search(
            [('origin', 'ilike', 'THHP - %s - %s' % (self.name, self.inpatient_id.name))], order='create_date DESC',
            limit=num_of_location)
        if pick_need_reverses:
            for pick_need_reverse in pick_need_reverses:
                date_done = pick_need_reverse.date_done

                fail_pick_count = self.env['stock.picking'].search_count([('name', 'ilike', pick_need_reverse.name)])
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
    def set_to_draft(self):
        # mở lại phiếu
        self.reverse_materials()
        res = self.write({'state': 'Draft'})

    def check_have_record(self,record):
        if isinstance(record.id, models.NewId):
            res = super(SHealthPatientRoundingManagement, self).create({
                'patient': self.patient.id,
                'doctor': self.doctor.id,
                'inpatient_id': self.inpatient_id.id,
                'evaluation_start_date': self.evaluation_start_date,
                'evaluation_end_date': self.evaluation_end_date,
                'temperature': self.temperature,
                'bpm': self.bpm,
                'respiratory_rate': self.respiratory_rate,
                'systolic': self.systolic,
                'diastolic': self.diastolic,
                'osat': self.osat,
                'evolution': self.evolution,
                'round_summary': self.round_summary,
                'execute': self.execute,
                'medicaments': self.medicaments.ids,
            })
            return res
        else:
            return record

    @api.multi
    def set_to_completed(self):
        # neu data phiếu chăm sóc chưa được tạo thì gọi hàm tạo
        res = self.check_have_record(self)

        # tru vat tu theo tieu hao của phiếu chi tiet cham soc hau phau
        if res.evaluation_end_date:
            evaluation_end_date = res.evaluation_end_date
        else:
            evaluation_end_date = res.evaluation_start_date if res.evaluation_start_date else fields.Datetime.now()

        vals = {}
        validate_str = ''
        for mat in res.medicaments:
            if mat.qty > 0:  # CHECK SO LUONG SU DUNG > 0
                quantity_on_hand = self.env['stock.quant']._get_available_quantity(mat.medicine.product_id,
                                                                                   mat.location_id)  # check quantity trong location
                if mat.uom_id != mat.medicine.uom_id:
                    mat.write({'qty': mat.uom_id._compute_quantity(mat.qty, mat.medicine.uom_id),
                               'uom_id': mat.medicine.uom_id.id})  # quy so suong su dung ve don vi chinh cua san pham

                if quantity_on_hand < mat.qty:
                    validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
                            mat.medicine.default_code, mat.medicine.name, str(quantity_on_hand), str(mat.uom_id.name), mat.location_id.name)
                else:  # truong one2many trong stock picking de tru cac product trong inventory
                    sub_vals = (0, 0, {
                        'name': 'THHP: ' + mat.medicine.product_id.name,
                        'origin': res.name,
                        'date': evaluation_end_date,
                        'company_id': self.env.user.company_id.id,
                        'date_expected': evaluation_end_date,
                        'date_done': evaluation_end_date,
                        'product_id': mat.medicine.product_id.id,
                        'product_uom_qty': mat.qty,
                        'product_uom': mat.uom_id.id,
                        'location_id': mat.location_id.id,
                        'location_dest_id': res.patient.partner_id.property_stock_customer.id,
                        'partner_id': res.patient.partner_id.id,
                        # xuat cho khach hang/benh nhan nao
                    })

                    if not vals.get(str(mat.location_id.id)):
                        vals[str(mat.location_id.id)] = [sub_vals]
                    else:
                        vals[str(mat.location_id.id)].append(sub_vals)

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
            for location_key in vals:
                pick_note = 'THHP - %s - %s - %s' % (
                res.name, res.inpatient_id.name, location_key)
                pick_vals = {'note': pick_note,
                             'origin': pick_note,
                             'partner_id': res.patient.partner_id.id,
                             'patient_id': self.patient.id,
                             'picking_type_id': picking_type,
                             'location_id': int(location_key),
                             'location_dest_id': res.patient.partner_id.property_stock_customer.id,
                             'date_done': evaluation_end_date,
                             'immediate_transfer': True,
                             'move_ids_without_package': vals[location_key]}
                fail_pick_name = self.env['stock.picking'].search(
                    [('origin', 'ilike', 'THHP - %s - %s - %s' % (res.name, res.inpatient_id.name, location_key))],
                    limit=1).name
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
                    move_line.move_line_ids.write({'date': evaluation_end_date})  # sửa ngày hoàn thành ở stock move line
                stock_picking.move_ids_without_package.write(
                    {'date': evaluation_end_date})  # sửa ngày hoàn thành ở stock move
                stock_picking.date_done = evaluation_end_date
                stock_picking.sci_date_done = evaluation_end_date

                stock_picking.create_date = res.evaluation_start_date

        elif validate_str != '':
            raise ValidationError(_(
                "Các loại Thuốc và Vật tư sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))

        # cap nhat vat tu cho phieu kham
        res.inpatient_id.walkin.update_walkin_material()

        res.write({'state': 'Completed', 'evaluation_end_date': evaluation_end_date})

        # log access patient
        data_log = self.env['sh.medical.patient.log'].search([('walkin', '=', res.inpatient_id.walkin.id)])
        data_hp = False
        for data in data_log:
            # nếu đã có data log cho ck khoa này rồi
            if data.department.id == res.inpatient_id.ward.id:
                data_hp = data
        # nếu chưa có data log=> tạo log
        if not data_hp:
            vals_log = {'walkin': res.inpatient_id.walkin.id,
                        'patient': res.patient.id,
                        'department': res.inpatient_id.ward.id,
                        'date_in': res.evaluation_start_date,
                        'date_out': res.evaluation_end_date}
            self.env['sh.medical.patient.log'].create(vals_log)
        else:
            data_hp.date_out = res.evaluation_end_date

    @api.multi
    def print_patient_evaluation(self):
        return self.env.ref('shealth_all_in_one.action_report_patient_rounding_evaluation').report_action(self)

class SHealthPatientInstructionMedicines(models.Model):
    _name = 'sh.medical.patient.instruction.medicines'
    _description = 'Patient Medicines For Instruction'

    MEDICAMENT_TYPE = [
        ('Medicine', 'Medicine'),
        ('Supplies', 'Supplies'),
    ]

    name = fields.Many2one('sh.medical.patient.instruction', string='Instruction')
    medicine = fields.Many2one('sh.medical.medicines', string='Medicines and Supply', domain=lambda self:[('categ_id','child_of',self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)], required=True)
    # medicine = fields.Many2one('sh.medical.medicines', string='Medicines', domain=[('medicament_type','=','Medicine')], required=True)
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    qty = fields.Float("Quantity", digits=dp.get_precision('Product Unit of Measure'),default=lambda *a: 1)
    notes = fields.Text('Comment')

    location_id = fields.Many2one('stock.location', 'Stock location', domain="[('usage', '=', 'internal')]")
    medicament_type = fields.Selection(MEDICAMENT_TYPE, related="medicine.medicament_type", string='Medicament Type',
                                       store=True)

    @api.onchange('qty', 'medicine')
    def onchange_qty(self):
        if self.qty <= 0 and self.medicine:
            raise UserError(_("Số lượng nhập phải lớn hơn 0!"))

    @api.onchange('medicine')
    def _change_product_id(self):
        self.uom_id = self.medicine.uom_id
        if self.medicament_type == 'Medicine':
            self.location_id = self.name.inpatient_id.bed.room.location_medicine_stock.id
        else:
            self.location_id = self.name.inpatient_id.bed.room.location_supply_stock.id


class SHealthPatientInstructionManagement(models.Model):
    _name = 'sh.medical.patient.instruction'
    _description = 'Patient Doctor Instruction Management'

    _order = "name"

    STATUS = [
        ('Draft', 'Draft'),
        ('Completed', 'Completed'),
    ]

    EVOLUTION = [
        ('Status Quo', 'Status Quo'),
        ('Improving', 'Improving'),
        ('Worsening', 'Worsening'),
    ]

    @api.multi
    def _get_patient_instruction(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    def get_anesthetist(self):
        if self.env.ref('__import__.khn_medical_job_gmhs',False):
            return [('is_pharmacist', '=', False), ('job_id', '=', self.env.ref('__import__.khn_medical_job_gmhs').id)]
        else:
            return [('is_pharmacist', '=', False)]

    name = fields.Char(string='Instruction #', size=128, readonly=True, default=lambda *a: '/')
    inpatient_id = fields.Many2one('sh.medical.inpatient', string='Registration Code', required=True, readonly=True, states={'Draft': [('readonly', False)]})
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True, states={'Draft': [('readonly', False)]})
    doctor = fields.Many2one('sh.medical.physician', string='Physician', help="Physician Name", domain=lambda self: self.get_anesthetist(), required=True, readonly=True,states={'Draft': [('readonly', False)]}, default=_get_patient_instruction)
    evaluation_start_date = fields.Datetime(string='Start date & time', required=True, readonly=True, states={'Draft': [('readonly', False)]}, default=lambda *a: datetime.datetime.now())
    evaluation_end_date = fields.Datetime(string='End date & time', readonly=True, states={'Draft': [('readonly', False)]})
    evolution = fields.Selection(EVOLUTION, string='Evolution', readonly=True, states={'Draft': [('readonly', False)]})
    round_summary = fields.Text(string="Round Summary", readonly=True, states={'Draft': [('readonly', False)]})
    ins_medicaments = fields.One2many('sh.medical.patient.instruction.medicines', 'name', string='Medicines', help="List of the medicines assigned in this instruction", readonly=True, states={'Draft': [('readonly', False)]})
    state = fields.Selection(STATUS, string='State',readonly=True, default=lambda *a: 'Draft')

    @api.onchange('evaluation_start_date')
    def _onchange_date(self):
        # if not self.evaluation_end_date:
        self.evaluation_end_date = self.evaluation_start_date

    @api.multi
    # Preventing deletion of a rounding details which is not in draft state
    def unlink(self):
        for nursing in self.filtered(lambda nursing: nursing.state not in ['Draft']):
            raise UserError(_('You can not delete instruction information which is not in "Draft" state !!'))
        return super(SHealthPatientInstructionManagement, self).unlink()

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.patient.instruction')
        vals['name'] = sequence
        return super(SHealthPatientInstructionManagement, self).create(vals)

    def reverse_materials(self):
        num_of_location = len(self.ins_medicaments.mapped('location_id'))
        pick_need_reverses = self.env['stock.picking'].search([('origin', 'ilike', 'THHP - %s - %s' % (self.name,self.inpatient_id.name))], order='create_date DESC', limit=num_of_location)
        if pick_need_reverses:
            for pick_need_reverse in pick_need_reverses:
                date_done = pick_need_reverse.date_done

                fail_pick_count = self.env['stock.picking'].search_count([('name', 'ilike', pick_need_reverse.name)])
                pick_need_reverse.name += '-FP%s' % fail_pick_count
                pick_need_reverse.move_ids_without_package.write(
                    {'reference': pick_need_reverse.name})  # sửa cả trường tham chiếu của move.line (Dịch chuyển kho)
                wizard = self.env['stock.return.picking'].with_context(active_id=pick_need_reverse.id, reopen_flag=True, no_check_quant=True).create({'picking_id': pick_need_reverse.id})
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
    def set_to_draft(self):
        # mở lại phiếu
        self.reverse_materials()
        res = self.write({'state': 'Draft'})

    def check_have_record(self,record):
        if isinstance(record.id, models.NewId):
            res = super(SHealthPatientInstructionManagement, self).create({
                'patient': record.patient.id,
                'doctor': record.doctor.id,
                'inpatient_id': record.inpatient_id.id,
                'evaluation_start_date': record.evaluation_start_date,
                'evaluation_end_date': record.evaluation_end_date,
                'round_summary': record.round_summary,
                'evolution': record.evolution,
                'ins_medicaments': record.ins_medicaments.ids,
            })
            return res
        else:
            return record

    def set_to_completed(self):
        # neu data phiếu y lệnh chưa được tạo thì gọi hàm tạo
        res = self.check_have_record(self)

        # tru vat tu theo tieu hao của phiếu chi tiet cham soc hau phau
        if res.evaluation_end_date:
            evaluation_end_date = res.evaluation_end_date
        else:
            evaluation_end_date = res.evaluation_start_date if res.evaluation_start_date else fields.Datetime.now()

        vals = {}
        validate_str = ''
        for mat in res.ins_medicaments:
            if mat.qty > 0:  # CHECK SO LUONG SU DUNG > 0
                quantity_on_hand = self.env['stock.quant']._get_available_quantity(mat.medicine.product_id,
                                                                                   mat.location_id)  # check quantity trong location
                if mat.uom_id != mat.medicine.uom_id:
                    mat.write({'qty': mat.uom_id._compute_quantity(mat.qty, mat.medicine.uom_id.id),
                               'uom_id': mat.medicine.uom_id.id})  # quy so suong su dung ve don vi chinh cua san pham

                if quantity_on_hand < mat.qty:
                    validate_str += "+ ""[%s]%s"": Còn %s %s tại ""%s"" \n" % (
                            mat.medicine.default_code, mat.medicine.name, str(quantity_on_hand), str(mat.uom_id.name), mat.location_id.name)
                else:  # truong one2many trong stock picking de tru cac product trong inventory
                    sub_vals = (0, 0, {
                        'name': 'THHP: ' + mat.medicine.product_id.name,
                        'origin': res.name,
                        'date': evaluation_end_date,
                        'company_id': self.env.user.company_id.id,
                        'date_expected': evaluation_end_date,
                        'date_done': evaluation_end_date,
                        'product_id': mat.medicine.product_id.id,
                        'product_uom_qty': mat.qty,
                        'product_uom': mat.uom_id.id,
                        'location_id': mat.location_id.id,
                        'location_dest_id': res.patient.partner_id.property_stock_customer.id,
                        'partner_id': res.patient.partner_id.id,
                        # xuat cho khach hang/benh nhan nao
                    })

                    if not vals.get(str(mat.location_id.id)):
                        vals[str(mat.location_id.id)] = [sub_vals]
                    else:
                        vals[str(mat.location_id.id)].append(sub_vals)

        # neu co vat tu tieu hao
        if vals and validate_str == '':
            # tao phieu xuat kho
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),
                                                                  ('warehouse_id', '=',
                                                                   self.env.ref('stock.warehouse0').id)],
                                                                 limit=1).id
            for location_key in vals:
                pick_note = 'THHP - %s - %s - %s' % (
                res.name, res.inpatient_id.name, location_key)
                pick_vals = {'note': pick_note,
                             'origin': pick_note,
                             'partner_id': res.patient.partner_id.id,
                             'patient_id': res.patient.id,
                             'picking_type_id': picking_type,
                             'location_id': int(location_key),
                             'location_dest_id': res.patient.partner_id.property_stock_customer.id,
                             'date_done': evaluation_end_date,
                             'immediate_transfer': True,
                             'move_ids_without_package': vals[location_key]}
                fail_pick_name = self.env['stock.picking'].search(
                    [('origin', 'ilike', 'THHP - %s - %s - %s' % (res.name, res.inpatient_id.name, location_key))],
                    limit=1).name
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
                    move_line.move_line_ids.write({'date': evaluation_end_date})  # sửa ngày hoàn thành ở stock move line
                stock_picking.move_ids_without_package.write(
                    {'date': evaluation_end_date})  # sửa ngày hoàn thành ở stock move
                stock_picking.date_done = evaluation_end_date
                stock_picking.sci_date_done = evaluation_end_date

                stock_picking.create_date = res.evaluation_start_date
        elif validate_str != '':
            raise ValidationError(_(
                "Các loại Thuốc và Vật tư sau đang không đủ số lượng tại tủ xuất:\n" + validate_str + "Hãy liên hệ với quản lý kho!"))

        # cap nhat vat tu cho phieu kham
        res.inpatient_id.walkin.update_walkin_material()

        res.write({'state': 'Completed', 'evaluation_end_date': evaluation_end_date})

    @api.multi
    def print_patient_instruction(self):
        return self.env.ref('shealth_all_in_one.action_report_patient_instruction').report_action(self)

class SHealthPatient(models.Model):
    _inherit = 'sh.medical.inpatient'

    roundings = fields.One2many('sh.medical.patient.rounding', 'inpatient_id', string='Roundings Details',
                                  states={'Draft': [('readonly', False)]})

    instructions = fields.One2many('sh.medical.patient.instruction', 'inpatient_id', string='Instruction Details',
                                states={'Draft': [('readonly', False)]})

# Patient Ambulatory Care Management

# class SHealthPatientAmbulatoryProcedures(models.Model):
#     _name = 'sh.medical.patient.ambulatory.procedure'
#     _description = 'Patient Procedures For Ambulatory'
#
#     name = fields.Many2one('sh.medical.patient.ambulatory', string='Ambulatory')
#     procedures = fields.Many2one('sh.medical.procedure', string='Procedures', required=True)
#     notes = fields.Text('Notes')
#
#
# class SHealthPatientAmbulatoryMedicines(models.Model):
#     _name = 'sh.medical.patient.ambulatory.medicines'
#     _description = 'Patient Medicines For Ambulatory'
#
#     name = fields.Many2one('sh.medical.patient.ambulatory', string='Ambulatory')
#     medicine = fields.Many2one('sh.medical.medicines', string='Medicines', domain=[('medicament_type','=','Medicine')], required=True)
#     qty = fields.Integer(string="Quantity", default=lambda *a: 1)
#     notes = fields.Text(string='Comment')
#
#
# class SHealthPatientAmbulatoryCare(models.Model):
#     _name = 'sh.medical.patient.ambulatory'
#     _description = 'Patient Ambulatory Management'
#
#     STATUS = [
#         ('Draft', 'Draft'),
#         ('Completed', 'Completed'),
#     ]
#
#     EVOLUTION = [
#         ('Initial', 'Initial'),
#         ('Status Quo', 'Status Quo'),
#         ('Improving', 'Improving'),
#         ('Worsening', 'Worsening'),
#     ]
#
#     @api.multi
#     def _get_patient_ambulatory(self):
#         """Return default physician value"""
#         therapist_obj = self.env['sh.medical.physician']
#         domain = [('sh_user_id', '=', self.env.uid)]
#         user_ids = therapist_obj.search(domain)
#         if user_ids:
#             return user_ids.id or False
#         else:
#             return False
#
#     name = fields.Char(string='Session #', size=128, readonly=True, default=lambda *a: '/')
#     evaluation_id = fields.Many2one('sh.medical.evaluation', string='Evaluation #', required=True, readonly=True, states={'Draft': [('readonly', False)]})
#     base_condition = fields.Many2one('sh.medical.pathology', string='Condition', required=True, readonly=True, states={'Draft': [('readonly', False)]})
#     patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True, readonly=True, states={'Draft': [('readonly', False)]})
#     doctor = fields.Many2one('sh.medical.physician', string='Physician', help="Physician Name", domain=[('is_pharmacist','=',False)], required=True, readonly=True,states={'Draft': [('readonly', False)]}, default=_get_patient_ambulatory)
#     ordering_doctor = fields.Many2one('sh.medical.physician', string='Requested by', help="Physician Name", domain=[('is_pharmacist','=',False)], readonly=True,states={'Draft': [('readonly', False)]})
#     evaluation_start_date = fields.Datetime(string='Start date & time', required=True, readonly=True, states={'Draft': [('readonly', False)]}, default= lambda *a: datetime.datetime.now())
#     evaluation_end_date = fields.Datetime(string='End date & time', readonly=True, states={'Draft': [('readonly', False)]})
#     systolic = fields.Integer(string='Systolic Pressure', readonly=True, states={'Draft': [('readonly', False)]})
#     diastolic = fields.Integer(string='Diastolic Pressure', readonly=True, states={'Draft': [('readonly', False)]})
#     bpm = fields.Integer(string='Heart Rate', help="Heart rate expressed in beats per minute", readonly=True, states={'Draft': [('readonly', False)]})
#     respiratory_rate = fields.Integer(string='Respiratory Rate', help="Respiratory rate expressed in breaths per minute", readonly=True, states={'Draft': [('readonly', False)]})
#     osat = fields.Integer(string='Oxygen Saturation', help="Oxygen Saturation(arterial)", readonly=True, states={'Draft': [('readonly', False)]})
#     temperature = fields.Float(string='Temperature', help="Temperature in celsius", readonly=True, states={'Draft': [('readonly', False)]})
#     glycemia = fields.Integer(string='Glycemia', help="Blood Glucose level", readonly=True, states={'Draft': [('readonly', False)]})
#     evolution = fields.Selection(EVOLUTION, string='Evolution', readonly=True, states={'Draft': [('readonly', False)]})
#     session_notes = fields.Text(string="Notes", readonly=True, states={'Draft': [('readonly', False)]})
#     procedures = fields.One2many('sh.medical.patient.ambulatory.procedure', 'name', string='Procedures', help="List of the procedures in this ambulatory. Please enter the first one as the main procedure", readonly=True, states={'Draft': [('readonly', False)]})
#     medicaments = fields.One2many('sh.medical.patient.ambulatory.medicines', 'name', string='Medicines', help="List of the medicines assigned in this ambulatory", readonly=True, states={'Draft': [('readonly', False)]})
#     state = fields.Selection(STATUS, string='State',readonly=True, default=lambda *a: 'Draft')
#
#
#     # Preventing deletion of a ambulatory care details which is not in draft state
#     @api.multi
#     def unlink(self):
#         for nursing in self.filtered(lambda nursing: nursing.state not in ['Draft']):
#             raise UserError(_('You can not delete information which is not in "Draft" state !!'))
#         return super(SHealthPatientAmbulatoryCare, self).unlink()
#
#
#     @api.model
#     def create(self, vals):
#         sequence = self.env['ir.sequence'].next_by_code('sh.medical.patient.ambulatory')
#         vals['name'] = sequence
#         return super(SHealthPatientAmbulatoryCare, self).create(vals)
#
#
#     @api.multi
#     def set_to_completed(self):
#         return self.write({'state': 'Completed','evaluation_end_date': datetime.datetime.now()})

class SHealthInpatient(models.Model):
    _inherit = 'sh.medical.inpatient'

    @api.multi
    def set_to_discharged(self):
        for inpatient in self:
            # còn y lệnh chưa xác nhận
            if len(inpatient.instructions.filtered(lambda ints: ints.state == "Draft")) > 0:
                raise UserError(_('Bạn không thể xác nhận kết thúc chăm sóc cho bệnh nhân khi có y lệnh chưa được xác nhận!'))

            # còn csph chưa xác nhận
            if len(inpatient.roundings.filtered(lambda rounds: rounds.state == "Draft")) > 0:
                raise UserError(
                    _('Bạn không thể xác nhận kết thúc chăm sóc cho bệnh nhân khi có phiếu cshp chưa được xác nhận!'))


        return super(SHealthInpatient, self).set_to_discharged()