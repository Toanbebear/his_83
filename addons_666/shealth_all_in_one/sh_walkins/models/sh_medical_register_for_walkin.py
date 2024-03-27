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
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
import datetime
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


def num2words_vnm(num):
    under_20 = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín', 'mười', 'mười một',
                'mười hai', 'mười ba', 'mười bốn', 'mười lăm', 'mười sáu', 'mười bảy', 'mười tám', 'mười chín']
    tens = ['hai mươi', 'ba mươi', 'bốn mươi', 'năm mươi', 'sáu mươi', 'bảy mươi', 'tám mươi', 'chín mươi']
    above_100 = {100: 'trăm', 1000: 'nghìn', 1000000: 'triệu', 1000000000: 'tỉ'}

    if num < 20:
        return under_20[num]

    elif num < 100:
        under_20[1], under_20[5] = 'mốt', 'lăm'  # thay cho một, năm
        result = tens[num // 10 - 2]
        if num % 10 > 0:  # nếu num chia 10 có số dư > 0 mới thêm ' ' và số đơn vị
            result += ' ' + under_20[num % 10]
        return result

    else:
        unit = max([key for key in above_100.keys() if key <= num])
        result = num2words_vnm(num // unit) + ' ' + above_100[unit]
        if num % unit != 0:
            if num > 1000 and num % unit < unit / 10:
                result += ' không trăm'
            if 1 < num % unit < 10:
                result += ' linh'
            result += ' ' + num2words_vnm(num % unit)
    return result.capitalize()


class WalkinImage(models.Model):
    _name = 'sh.medical.walkin.image'
    _description = 'Ảnh trong phiếu khám'

    name = fields.Char('Tên')
    image = fields.Binary('Ảnh', attachment=True)
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', 'Phiếu khám liên quan', copy=True)


class SHealthWalkinMaterial(models.Model):
    _name = 'sh.medical.walkin.material'
    _description = 'All material of the Walkin'

    NOTE = [
        ('Labtest', 'Material of Labtest'),
        ('Imaging', 'Material of Imaging'),
        ('Surgery', 'Material of Surgery'),
        ('Specialty', 'Material of Specialty Service'),
        ('Inpatient', 'Material of Inpatient'),
        ('Evaluation', 'Material of Evaluation'),
        ('Medicine', 'Thuốc cấp về'),
        # ('Extra', 'Material of Extra Service'),
    ]

    sequence = fields.Integer('Sequence',
                              default=lambda self: self.env['ir.sequence'].next_by_code('sequence'))  # Số thứ tự
    imaging_id = fields.Many2one('sh.medical.imaging', string='Imaging Test')
    product_id = fields.Many2one('sh.medical.medicines', string='Product', required=True,
                                 domain=lambda self: [('categ_id', 'child_of',
                                                       self.env.ref('shealth_all_in_one.sh_sci_medical_product').id)])
    init_quantity = fields.Float('Initial Quantity',
                                 digits=dp.get_precision('Product Unit of Measure'))  # số lượng bom ban đầu của vật tư
    quantity = fields.Float('Quantity',
                            digits=dp.get_precision('Product Unit of Measure'))  # số lượng sử dụng vật tư
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure')
    note = fields.Selection(NOTE, 'Material note')
    interner_note = fields.Char('Interner note')
    is_readonly = fields.Boolean('Is readonly', default=False)

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', readonly=True)

    institution = fields.Many2one('sh.medical.health.center', string='Health Center', required=True)
    department = fields.Many2one('sh.medical.health.center.ward', string='Department', required=True)
    location_id = fields.Many2one('stock.location', 'Tủ xuất')

    _order = "sequence"

    @api.onchange('product_id')
    def _change_product_id(self):
        self.uom_id = self.product_id.uom_id

        return {'domain': {'uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('uom_id')
    def _change_uom_id(self):
        if self.uom_id.category_id != self.product_id.uom_id.category_id:
            self.uom_id = self.product_id.uom_id
            raise Warning(
                _('The Walkin Unit of Measure and the Material Unit of Measure must be in the same category.'))


class SHealthPatientLog(models.Model):
    _name = 'sh.medical.patient.log'
    _description = 'All log access Room of the patient'

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #')
    patient = fields.Many2one('sh.medical.patient', string='Patient')
    department = fields.Many2one('sh.medical.health.center.ward', string='Department access')

    date_in = fields.Datetime('Date in')
    date_out = fields.Datetime('Date out')

    _order = "date_in"


class SHealthAppointmentWalkin(models.Model):
    _name = "sh.medical.appointment.register.walkin"
    _description = "Information of Walkin"

    _inherit = [
        'mail.thread']

    _order = "date desc"

    MARITAL_STATUS = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Widowed', 'Widowed'),
        ('Divorced', 'Divorced'),
        ('Separated', 'Separated'),
    ]

    SEX = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    BLOOD_TYPE = [
        ('A', 'A'),
        ('B', 'B'),
        ('AB', 'AB'),
        ('O', 'O'),
    ]

    RH = [
        ('+', '+'),
        ('-', '-'),
    ]

    WALKIN_STATUS = [
        ('Scheduled', 'Scheduled'),
        ('WaitPayment', 'Chờ thu tiền'),
        ('Payment', 'Đã thu tiền'),
        ('InProgress', 'In progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        # ('Invoiced', 'Invoiced'),
    ]

    REASON_CHECK = [
        ('Advisory', 'Tư vấn'),
        ('Recheck', 'Tái khám'),
        ('Guarantee', 'Bảo hành'),
        ('Hospitalize', 'Nhập viện'),
    ]

    HANDLE = [
        ('discharge', 'Ra viện'),
        ('outpatient', 'Điều trị ngoại trú'),
        ('allow', 'Xin về'),
        ('escaped', 'Trốn viện'),
        ('transit', 'Chuyển tuyến'),
        ('dead', 'Tử vong'),
    ]

    @api.multi
    def _get_physician(self):
        """Return default physician value"""
        therapist_obj = self.env['sh.medical.physician']
        domain = [('sh_user_id', '=', self.env.uid)]
        user_ids = therapist_obj.search(domain)
        if user_ids:
            return user_ids.id or False
        else:
            return False

    def get_physician_kb(self):
        return [('is_pharmacist', '=', False)]
        # if self.env.ref('__import__.khn_medical_job_kb',False):
        #     return [('is_pharmacist', '=', False), ('job_id', '=', self.env.ref('__import__.khn_medical_job_kb').id)]
        # else:
        #     return [('is_pharmacist', '=', False)]

    name = fields.Char(string='Queue #', size=128, required=True, default=lambda *a: '/',
                       states={'Completed': [('readonly', True)]}, track_visibility='always')
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True,
                              readonly=False, states={'Completed': [('readonly', True)]})
    dob = fields.Date(string='Date of Birth', related="patient.dob", store=True, track_visibility='onchange')
    sex = fields.Selection(SEX, string='Sex', related="patient.sex", store=True, track_visibility='onchange')
    marital_status = fields.Selection(MARITAL_STATUS, string='Marital Status', related="patient.marital_status",
                                      store=True, track_visibility='onchange')
    blood_type = fields.Selection(BLOOD_TYPE, string='Blood Type', related="patient.blood_type", store=True,
                                  track_visibility='onchange')
    rh = fields.Selection(RH, string='Rh', readonly=False, related="patient.rh", store=True,
                          track_visibility='onchange')
    doctor = fields.Many2one('sh.medical.physician', string='Responsible Physician', readonly=False,
                             states={'Completed': [('readonly', True)]}, domain=lambda self: self.get_physician_kb(),
                             default=_get_physician, track_visibility='onchange')
    state = fields.Selection(WALKIN_STATUS, string='State', readonly=False, states={'Completed': [('readonly', True)]},
                             default=lambda *a: 'Scheduled', track_visibility='onchange')
    comments = fields.Text(string='Comments', readonly=False, states={'Completed': [('readonly', True)]},
                           track_visibility='onchange')
    date = fields.Datetime(string='Day of the examination', compute="_compute_date", required=True, store=True,
                           readonly=False, states={'Completed': [('readonly', True)]},
                           default=lambda self: fields.Datetime.now(), track_visibility='onchange')
    evaluation_ids = fields.One2many('sh.medical.evaluation', 'walkin', string='Evaluation', readonly=False,
                                     states={'Completed': [('readonly', True)]})
    prescription_ids = fields.One2many('sh.medical.prescription', 'walkin', string='Prescriptions', readonly=False,
                                       states={'Completed': [('readonly', True)]})
    lab_test_ids = fields.One2many('sh.medical.lab.test', 'walkin', string='Lab Tests', readonly=False,
                                   states={'Completed': [('readonly', True)]})
    imaging_ids = fields.One2many('sh.medical.imaging', 'walkin', string='Imaging Tests', readonly=False,
                                  states={'Completed': [('readonly', True)]})
    surgeries_ids = fields.One2many('sh.medical.surgery', 'walkin', string='Surgeries Tests', readonly=False,
                                    states={'Completed': [('readonly', True)]})
    specialty_ids = fields.One2many('sh.medical.specialty', 'walkin', string='Specialty Tests', readonly=False,
                                    states={'Completed': [('readonly', True)]})
    inpatient_ids = fields.One2many('sh.medical.inpatient', 'walkin', string='Inpatient Admissions', readonly=False,
                                    states={'Completed': [('readonly', True)]})
    # vaccine_ids = fields.One2many('sh.medical.vaccines', 'walkin', string='Vaccines', readonly=False, states={'Completed': [('readonly', True)]})

    institution = fields.Many2one('sh.medical.health.center', string='Health Center', required=True, readonly=False,
                                  states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    department = fields.Many2one('sh.medical.health.center.ward', string='Department',
                                 help="Department of the selected Health Center",
                                 domain="[('institution','=',institution)]", readonly=False,
                                 states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    # reason_check = fields.Selection(REASON_CHECK, 'Reason Check', readonly=False, states={'Completed': [('readonly', True)]}, default=lambda *a: 'Advisory', track_visibility='onchange')
    reason_check = fields.Text('Reason Check', related="reception_id.reason", readonly=False,
                               states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    # service = fields.Many2one('sh.medical.health.center.service', string='Service', readonly=False, states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    service = fields.Many2many('sh.medical.health.center.service', 'sh_walkin_service_rel', 'walkin_id', 'service_id',
                               readonly=False, states={'Completed': [('readonly', True)]}, track_visibility='onchange',
                               string='Services')
    service_room = fields.Many2one('sh.medical.health.center.ot', string='Room perform',
                                   domain="[('department', '=', department)]", readonly=False,
                                   states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    service_expected = fields.Many2many('sh.medical.health.center.service', 'sh_walkin_service_expected_rel',
                                        'walkin_id', 'service_id', readonly=True, track_visibility='onchange',
                                        string='Services Expected')
    # service_expected = fields.Many2one('sh.medical.health.center.service', string='Service expected', readonly=False, states={'Completed': [('readonly', True)]}, track_visibility='onchange')
    date_re_exam = fields.Datetime(string='Date Re-exam', readonly=False, states={'Completed': [('readonly', True)]},
                                   track_visibility='onchange')
    date_out = fields.Datetime(string='Ngày ra viện', readonly=False, states={'Completed': [('readonly', True)]},
                               track_visibility='onchange')
    # taskmaster = fields.Many2one('res.users', string='Taskmaster', readonly=True, track_visibility='onchange')

    # thong tin vat tu
    material_ids = fields.One2many('sh.medical.walkin.material', 'walkin', string="Material Information")

    patient_log = fields.One2many('sh.medical.patient.log', 'walkin', string='History')

    # liên kết reception
    reception_id = fields.Many2one('sh.reception', string='Reception')

    # count
    lab_test_count = fields.Integer('Lab test count', compute="count_lab_test")
    img_test_count = fields.Integer('Imaging test count', compute="count_img_test")
    surgery_count = fields.Integer('Surgery count', compute="count_surgery")
    specialty_count = fields.Integer('Specialty count', compute="count_specialty")

    lab_test_done_count = fields.Integer('Lab test completed count', readonly=True)
    img_test_done_count = fields.Integer('Imaging completed test count', readonly=True)
    surgery_done_count = fields.Integer('Surgery Done count', readonly=True)
    specialty_done_count = fields.Integer('Specialty Done count', readonly=True)

    has_lab_result = fields.Boolean('Đã có KQ XN', readonly=True, store=True)
    has_img_result = fields.Boolean('Đã có KQ CĐHA', readonly=True, store=True)

    # money_spent = fields.Float('Money spent', compute="sum_money_spent")

    pathology = fields.Many2many('sh.medical.pathology', string='Condition', help="Base Condition / Reason",
                                readonly=False, states={'Completed': [('readonly', True)]})

    is_over_material = fields.Boolean('Over material', default=False)
    user_approval = fields.Many2one('res.users', string='User approval', readonly=True, track_visibility='onchange')

    # phiếu khám gốc
    root_walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Root walkin',
                                  domain="[('patient','=',patient)]",
                                  hint="Dùng liên kết các phiếu khám của dịch vụ liệu trình hoặc tái khám",
                                  states={'Completed': [('readonly', True)]}, track_visibility='onchange')

    @api.onchange('root_walkin')
    def onchange_root_walkin(self):
        if self.root_walkin:
            self.pathological_process = self.root_walkin.pathological_process
            self.surgery_history = self.root_walkin.surgery_history
            self.allergy_history = self.root_walkin.allergy_history
            self.family_history = self.root_walkin.family_history
            self.physical_exam = self.root_walkin.physical_exam
            self.cyclic_info = self.root_walkin.cyclic_info
            self.respiratory_exam = self.root_walkin.respiratory_exam
            self.digest_exam = self.root_walkin.digest_exam
            self.reins_exam = self.root_walkin.reins_exam
            self.nerve_exam = self.root_walkin.nerve_exam
            self.other_exam = self.root_walkin.other_exam
            self.specialty_exam = self.root_walkin.specialty_exam
            self.temperature = self.root_walkin.temperature
            self.systolic = self.root_walkin.systolic
            self.respiratory_rate = self.root_walkin.respiratory_rate
            self.bpm = self.root_walkin.bpm
            self.weight = self.root_walkin.weight
            self.height = self.root_walkin.height
            self.service = self.root_walkin.service

    # trường ẩn hiện phiếu pttt theo dịch vụ
    flag_surgery = fields.Boolean('Flag surgery', default=False)

    handle = fields.Selection(HANDLE, string='Handle', readonly=False, states={'Completed': [('readonly', True)]},
                              track_visibility='onchange')

    payment_ids = fields.One2many('account.payment', 'walkin', string='Phiếu thu')
    lock = fields.Boolean('Khóa phiếu')

    index_by_day = fields.Integer('Số thứ tự', compute="_compute_date_to_index")

    doctor_surgeon = fields.Many2one('sh.medical.physician', string='Bác sĩ phẫu thuật',
                                     compute="_compute_doctor_surgeon")
    doctor_anesthetist = fields.Many2one('sh.medical.physician', string='Bác sĩ gây mê',
                                         compute="_compute_doctor_surgeon")

    walkin_image_ids = fields.One2many('sh.medical.walkin.image', 'walkin', string='Images')

    @api.depends('surgeries_ids')
    def _compute_doctor_surgeon(self):
        for record in self:
            if record.surgeries_ids:
                record.doctor_surgeon = record.surgeries_ids[0].surgeon
                record.doctor_anesthetist = record.surgeries_ids[0].anesthetist

    def _get_specialty_exam(self):
        return self.reason_check

    # thông tin thăm khám
    pathological_process = fields.Text('Quá trình bệnh lý')
    surgery_history = fields.Text('Tiền sử ngoại khoa', default="Không")
    medical_history = fields.Text('Tiền sử nội khoa', default="Không")
    allergy_history = fields.Text('Tiền sử dị ứng', default="Không")
    family_history = fields.Text('Tiền sử gia đình', default="Không")
    physical_exam = fields.Text('Toàn thân',
                                default="""-	Thể trạng khá.\n-	Da không xanh , niêm mạc hồng.\n-	Tuyến giáp không to.\n-	Hạnh ngoại biên không sờ thấy.""")
    cyclic_info = fields.Text('Tuần hoàn', default="Nhịp tim đều : 0 lần/ phút, Tiếng tim T1T2 bình thường.")
    respiratory_exam = fields.Text('Hô hấp', default="Thở êm, rì rào phế nang đều rõ 2 bên.")
    digest_exam = fields.Text('Tiêu hóa', default="Bụng mềm, Gan lách không to.")
    reins_exam = fields.Text('Thận – Tiết niệu – Sinh dục', default="Khám sơ bộ bình thường.")
    nerve_exam = fields.Text('Thần kinh', default="Ý thức tốt, không có dấu hiệu thần kinh khu trú.")
    other_exam = fields.Text('Các cơ quan khác', default="chưa phát hiện dấu hiệu bệnh lý.")
    specialty_exam = fields.Text('Chuyên khoa')

    systolic = fields.Integer(string='Systolic Pressure')
    diastolic = fields.Integer(string='Diastolic Pressure')
    bpm = fields.Integer(string='Heart Rate', help="Heart rate expressed in beats per minute")
    respiratory_rate = fields.Integer(string='Respiratory Rate',
                                      help="Respiratory rate expressed in breaths per minute")
    temperature = fields.Float(string='Temperature (celsius)')
    weight = fields.Float(string='Weight (kg)')
    height = fields.Float(string='Height (cm)')
    bmi = fields.Float(string='Body Mass Index (BMI)')
    info_diagnosis = fields.Text(string='Presumptive Diagnosis')
    directions = fields.Text(string='Plan')

    @api.onchange('bpm')
    def onchange_bpm(self):
        self.cyclic_info = "Nhịp tim đều : %s lần/ phút, Tiếng tim T1T2 bình thường." % str(self.bpm)

    @api.onchange('height', 'weight')
    def onchange_height_weight(self):
        res = {}
        if self.height:
            self.bmi = self.weight / ((self.height / 100) ** 2)
        else:
            self.bmi = 0
        return res

    @api.depends('date', 'service_room')
    def _compute_date_to_index(self):
        for record in self:
            start = record.date.strftime("%Y-%m-%d 00:00:00")
            end = record.date.strftime("%Y-%m-%d 23:59:59")
            data = self.env['sh.medical.appointment.register.walkin'].search(
                [('date', '>=', start), ('date', '<=', end), ('service_room', '=', record.service_room.id)],
                order="date")
            # print(self.id)
            if len(data) > 0:
                list_date = data.mapped('date')
                list_date.append(record.date)
                list_date.sort()
                record.index_by_day = list_date.index(record.date) + 1
            else:
                record.index_by_day = 1

    @api.depends('reception_id.reception_date')
    def _compute_date(self):
        for record in self:
            if record.reception_id.reception_date:
                record.date = datetime.datetime.strptime(
                    record.reception_id.reception_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S") + timedelta(
                    minutes=10) or fields.Datetime.now()
            else:
                record.date = fields.Datetime.now()

    @api.depends('service', 'lab_test_ids', 'imaging_ids')
    def _compute_service_case(self):
        for record in self:
            # có chọn dịch vụ
            if record.service:
                record.compute_service = self.env.ref('shealth_all_in_one.sh_product_service_kb01').product_id + \
                                         record.lab_test_ids.filtered(
                                             lambda m: m.state in ['Test In Progress', 'Completed']). \
                                             mapped('test_type.product_id') + \
                                         record.imaging_ids.filtered(
                                             lambda m: m.state in ['Test In Progress', 'Completed']). \
                                             mapped('test_type.product_id') + \
                                         record.service.mapped('product_id')

    compute_service = fields.Many2many('product.product', compute=_compute_service_case)

    @api.depends('patient_log')
    def _compute_patient_log(self):
        for wk in self:
            if wk.patient_log:
                for log in wk.patient_log:
                    if not log.date_out:
                        wk.department_current = log.department

    department_current = fields.Many2one('sh.medical.health.center.ward', string='Department',
                                         help="Department Current", compute=_compute_patient_log, store="True")

    _sql_constraints = [
        ('full_name_uniq', 'unique (name)', 'The Queue Number must be unique')
    ]

    # tong hop vat tu da dung trong phieu
    # @api.one
    # @api.depends('lab_test_ids', 'imaging_ids', 'surgeries_ids')
    # def _compute_materials(self):
    #     # self.update_walkin_material()
    #     self.material_ids = False
    #
    #     print(self.lab_test_ids)
    #     mats = []
    #     seq_mat = 0
    #     for lab in self.lab_test_ids:
    #         for lab_mats in lab.lab_test_material_ids:
    #             seq_mat += 1
    #             mats.append((0, 0, {'product_id': lab_mats.product_id.id,
    #                                 'sequence': seq_mat,
    #                                 'quantity': lab_mats.quantity,
    #                                 'institution': lab.institution.id,
    #                                 'department': lab.department.id,
    #                                 'uom_id': lab_mats.uom_id.id,
    #                                 'is_readonly': True,
    #                                 'walkin': self.id,
    #                                 'note': 'Labtest',
    #                                 'interner_note': 'Labtest'}))
    #
    #     for img in self.imaging_ids:
    #         for img_mats in img.imaging_material_ids:
    #             seq_mat += 1
    #             mats.append((0, 0, {'product_id': img_mats.product_id.id,
    #                                 'sequence': seq_mat,
    #                                 'quantity': img_mats.quantity,
    #                                 'institution': img.institution.id,
    #                                 'department': img.department.id,
    #                                 'uom_id': img_mats.uom_id.id,
    #                                 'is_readonly': True,
    #                                 'walkin': self.id,
    #                                 'note': 'Imaging',
    #                                 'interner_note': 'Imaging'}))
    #
    #     for sur in self.surgeries_ids:
    #         for sur_mats in sur.supplies:
    #             seq_mat += 1
    #             mats.append((0, 0, {'product_id': sur_mats.supply.id,
    #                                 'sequence': seq_mat,
    #                                 'quantity': sur_mats.qty_used,
    #                                 'institution': sur.institution.id,
    #                                 'department': sur.department.id,
    #                                 'uom_id': sur_mats.uom_id.id,
    #                                 'is_readonly': True,
    #                                 'walkin': self.id,
    #                                 'note': 'Surgery',
    #                                 'interner_note': 'Surgery'}))
    #
    #     print(mats)
    #     self.material_ids = mats

    # @api.one
    # @api.depends('lab_test_ids','imaging_ids','surgeries_ids','specialty_ids','state')
    # def sum_money_spent(self):
    #     ms = 0
    #     # ghi nhan tien dich vu
    #     if self.state == 'Completed':
    #         ms = self.service.list_price
    #     # elif self.surgery_done_count == self.surgery_count and self.surgery_count > 0:
    #     #     ms = self.service.list_price
    #     # elif self.specialty_done_count == self.specialty_count and self.specialty_count > 0:
    #     #     ms = self.service.list_price
    #     else:
    #         for lab in self.lab_test_ids:
    #             if lab.state == 'Test In Progress' or lab.state == 'Completed':
    #                 ms += lab.test_type.list_price
    #
    #         for img in self.imaging_ids:
    #             if img.state == 'Test In Progress' or img.state == 'Completed':
    #                 ms += img.test_type.list_price
    #
    #     self.money_spent = ms

    # view labtest by walkin
    @api.multi
    def view_labtest_by_walkin(self):
        return {
            'name': _('View List LabTest by Walkin'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_lab_test_tree').id,
            'res_model': 'sh.medical.lab.test',  # model want to display
            'target': 'new',  # if you want popup
            'domain': [('walkin', '=', self.id)],
        }

    #  TRẢ KẾT QUẢ XN
    @api.multi
    def return_result_labtest_by_walkin(self):
        self.env['ir.actions.actions'].clear_caches()

        return {
            'name': _('TRẢ KẾT QUẢ XN'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.walkin_labtest_result_view_form').id,
            'res_model': 'walkin.labtest.result',  # model want to display
            'target': 'new',  # if you want popup
        }

    # view imaging by walkin
    @api.multi
    def view_imaging_by_walkin(self):
        return {
            'name': _('View List Imaging by Walkin'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_imaging_test_tree').id,
            'res_model': 'sh.medical.imaging',  # model want to display
            'target': 'new',  # if you want popup
            'domain': [('walkin', '=', self.id)],
        }

    # view surgery by walkin
    @api.multi
    def view_surgery_by_walkin(self):
        return {
            'name': _('View List Surgery by Walkin'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_surgery_tree').id,
            'res_model': 'sh.medical.surgery',  # model want to display
            'target': 'new',  # if you want popup
            'domain': [('walkin', '=', self.id)],
        }

    # view specialty by walkin
    @api.multi
    def view_specialty_by_walkin(self):
        return {
            'name': _('Xem Phiếu Chuyên khoa của Phiếu khám'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_specialty_tree').id,
            'res_model': 'sh.medical.specialty',  # model want to display
            'target': 'new',  # if you want popup
            'domain': [('walkin', '=', self.id)],
        }

    @api.multi
    def view_walkin_material(self):
        view_id = self.env.ref('shealth_all_in_one.sh_medical_materials_of_walkin_tree').id
        return {'type': 'ir.actions.act_window',
                'name': _('Materials of Walkin Details'),
                'res_model': 'sh.medical.walkin.material',
                'target': 'fullscreen',
                'view_mode': 'tree',
                'view_type': 'form',
                'domain': [('walkin', '=', self.id)],
                'context': {'search_default_group_department': True},
                'views': [[view_id, 'tree']],
                }

    # ham dem xet nghiem
    @api.one
    @api.depends('lab_test_ids')
    def count_lab_test(self):
        self.lab_test_count = len(self.lab_test_ids.filtered(lambda s: s.state != 'Cancelled'))
        self.lab_test_done_count = len(self.lab_test_ids.filtered(lambda s: s.state == 'Completed'))
        self.has_lab_result = True if self.lab_test_count - self.lab_test_done_count == 0 else False

    # ham dem cdha
    @api.one
    @api.depends('imaging_ids')
    def count_img_test(self):
        self.img_test_count = len(self.imaging_ids.filtered(lambda s: s.state != 'Cancelled'))
        self.img_test_done_count = len(self.imaging_ids.filtered(lambda s: s.state == 'Completed'))
        self.has_img_result = True if self.img_test_count - self.img_test_done_count == 0 else False

    # ham dem pttt
    @api.one
    @api.depends('surgeries_ids.state')
    def count_surgery(self):
        self.surgery_count = len(self.surgeries_ids.filtered(lambda s: s.state != 'Cancelled'))
        self.surgery_done_count = len(self.surgeries_ids.filtered(lambda s: s.state in ['Done', 'Signed']))

    # ham dem specialty
    @api.one
    @api.depends('specialty_ids.state')
    def count_specialty(self):
        self.specialty_count = len(self.specialty_ids.filtered(lambda s: s.state != 'Cancelled'))
        self.specialty_done_count = len(self.specialty_ids.filtered(lambda s: s.state == 'Done'))

    @api.onchange('institution')
    def _onchange_institution(self):
        # set khoa mac dinh la khoa kham benh cua co so y te
        if self.institution:
            exam_dep = self.env['sh.medical.health.center.ward'].search(
                [('institution', '=', self.institution.id), ('type', '=', 'Examination')], limit=1)
            self.department = exam_dep
            self.service_room = ''

    # @api.onchange('pathology')
    # def _onchange_pathology(self):
    #     if self.service:#xoa nhung dich vu ko cung nhom benh
    #         for ser in self.service:
    #             if ser.pathology.id != self.pathology.id:
    #                 self.service = [(2, ser.id)]

    @api.onchange('doctor')
    def _onchange_doctor(self):
        if self.doctor:  # ghi nhận bac si yêu cau o cac phieu can lam sang
            for labtest in self.lab_test_ids:
                labtest.requestor = self.doctor

            for imaging in self.imaging_ids:
                imaging.requestor = self.doctor

            for surgery in self.surgeries_ids:
                surgery.surgeon = self.doctor

            for specialty in self.specialty_ids:
                specialty.physician = self.doctor

    @api.onchange('service')
    def _onchange_services_case(self):
        if self.service:
            # self.material_ids = False
            self.flag_surgery = self.service[0].is_surgeries
            # self.institution = self.service[0].institution.id
            self.pathology = [(6, 0, self.service.mapped('pathology').ids)]
            # self.info_diagnosis = self.service.mapped('diagnose')
            diagnose = set(self.service.mapped('diagnose'))
            self.info_diagnosis = ', '.join(diagnose)

            if not self.department and self.service_room:
                self.department = self.service_room.department

                # Nếu phiếu đã thu tiền
                if self.state not in ['Scheduled', 'WaitPayment', 'Payment']:
                    payment_detail = self.env['account.payment'].browse(self.payment_ids[0].id or False)
                    # đã có phiếu thu
                    if len(payment_detail) > 0:
                        service_name = ''
                        total = 0
                        for ser in self.service:
                            total += ser.list_price
                            service_name += ser.name + ";"

                        payment_detail.write({
                            'amount': total,
                            'note': "Thu tiền dịch vụ: " + service_name,
                            'text_total': num2words_vnm(int(total)) + " đồng",
                        })

    #     marterial_wakin = []
    #     id_marterial_wakin = {}
    #
    #     # START - xoa nhung phieu dang nhap khi change service
    #     if self.lab_test_ids:
    #         for lt_id in self.lab_test_ids:
    #             if lt_id.state == 'Draft':
    #                 self.lab_test_ids = [(2,lt_id.id)]
    #
    #     lab_test_wakin = []
    #     id_lab_test_wakin = self.lab_test_ids.mapped('test_type').ids
    #
    #     if self.imaging_ids:
    #         for img_id in self.imaging_ids:
    #             if img_id.state == 'Draft':
    #                 self.imaging_ids = [(2, img_id.id)]
    #
    #     img_test_wakin = []
    #     id_img_test_wakin = self.imaging_ids.mapped('test_type').ids
    #
    #     if self.surgeries_ids:
    #         for sur_id in self.surgeries_ids:
    #             if sur_id.state == 'Draft':
    #                 self.surgeries_ids = [(2, sur_id.id)]
    #             # else:
    #             #     raise ValidationError(_('You can not remove surgery not in Draft!'))
    #
    #     surgery_wakin = []
    #     id_surgery_test_wakin = self.surgeries_ids.mapped('services').ids
    #
    #     if self.specialty_ids:
    #         for spec_id in self.specialty_ids:
    #             if spec_id.state == 'Draft':
    #                 self.specialty_ids = [(2, spec_id.id)]
    #             # else:
    #             #     raise ValidationError(_('You can not remove service not in Draft!'))
    #     specialty_wakin = []
    #     id_specialty_test_wakin = self.specialty_ids.mapped('services').ids
    #
    #     # if self.prescription_ids:
    #     #     for pres_id in self.prescription_ids:
    #     #         if pres_id.state == 'Draft':
    #     #             self.prescription_ids = [(2, pres_id.id)]
    #     # prescription_wakin = []
    #
    #     # END - xoa nhung phieu dang nhap khi change service
    #
    #     #TAO CÁC PHIEU XN, CĐHA, PTTT, CK NẾU CÓ
    #     seq_mat = 0
    #     for ser in self.service:
    #         # add vat tu tieu hao tong - ban dau
    #         # for mats in ser.material_ids:
    #         #     # if mats.product_id.id not in id_marterial_wakin: #chua co thi tao moi vtth
    #         #     #     id_marterial_wakin.append(mats.product_id.id)
    #         #     walkin_dict_key = str(mats.product_id.id) + '-' + str(mats.department.id)
    #         #     if not id_marterial_wakin.get(walkin_dict_key):
    #         #         seq_mat += 1
    #         #         id_marterial_wakin[walkin_dict_key] = seq_mat
    #         #         marterial_wakin.append((0, 0, {'product_id': mats.product_id.id,
    #         #                                      'sequence': seq_mat,
    #         #                                      'quantity': mats.quantity,
    #         #                                      'institution': mats.institution.id,
    #         #                                      'department': mats.department.id,
    #         #                                      'uom_id': mats.uom_id.id,
    #         #                                      'is_readonly': True,
    #         #                                      'note': mats.note,
    #         #                                      'interner_note': mats.note}))
    #         #     #co vtth roi thi lay so luong lon nhat
    #         #     elif mats.quantity > marterial_wakin[id_marterial_wakin[walkin_dict_key]-1][2]['quantity']:
    #         #         marterial_wakin[id_marterial_wakin[walkin_dict_key]-1][2]['quantity'] = mats.quantity
    #             # else:
    #
    #         # add lab test
    #         for lab in ser.lab_type_ids:
    #             if lab.id not in id_lab_test_wakin:
    #                 lab_department = self.env['sh.medical.health.center.ward'].search(
    #                     [('institution', '=', self.institution.id), ('type', '=', 'Laboratory')], limit=1)
    #
    #                 id_lab_test_wakin.append(lab.id) # co roi se khong add thêm nữa
    #                 lab_test_wakin.append((0, 0, {
    #                                             'institution': self.institution.id,
    #                                            'department': lab_department,
    #                                            'test_type': lab.id,
    #                                            'has_child': lab.has_child,
    #                                            'normal_range': lab.normal_range,
    #                                            'patient': self.patient.id,
    #                                            'date_requested': datetime.datetime.now(),
    #                                            'requestor':self.doctor.id,
    #                                            # 'pathologist':self.doctor.id,
    #                                            'lab_test_material_ids':[],
    #                                            'lab_test_criteria':[],
    #                                            'walkin': self._origin.id,
    #                                            'state': 'Draft'}))
    #
    #         # add imaging test
    #         for img in ser.imaging_type_ids:
    #             if img.id not in id_img_test_wakin:
    #                 img_department = self.env['sh.medical.health.center.ward'].search(
    #                     [('institution', '=', self.institution.id), ('type', '=', 'Imaging')], limit=1)
    #
    #                 id_img_test_wakin.append(img.id) # co roi se khong add thêm nữa
    #                 img_test_wakin.append((0, 0, {
    #                                           'institution': self.institution.id,
    #                                           'department': img_department,
    #                                           'test_type': img.id,
    #                                           'patient': self.patient.id,
    #                                           'date_requested': datetime.datetime.now(),
    #                                           'requestor': self.doctor.id,
    #                                           # 'pathologist': self.doctor.id,
    #                                           'imaging_material_ids': [],
    #                                           'walkin': self._origin.id,
    #                                           'state': 'Draft'}))
    #
    #         # material_of_walkin = res.walkin.material_ids
    #         # sg_supply_data = []
    #         # for sg in material_of_walkin:
    #         #     if sg.note == 'Surgery':
    #         #         sg_supply_data.append((0, 0, {'note': sg.note,
    #         #                                'supply': sg.product_id.id,
    #         #                                'qty': sg.quantity,
    #         #                                'qty_use': sg.uom_id.id,
    #         #                                        'uom_id': sg.uom_id.id}))
    #
    #         #add surgeries (neu co)
    #         if ser.is_surgeries:
    #             sur_department = ser.service_department.filtered(lambda s: s.institution == self.institution and s.type == 'Surgery')
    #             sur_room = ser.service_room.filtered(lambda s: s.institution == self.institution)
    #             if sur_room:
    #                 sur_room = sur_room[0]
    #
    #             if ser.id not in id_surgery_test_wakin:
    #                 surgery_wakin.append((0, 0, {
    #                                           'institution': self.institution.id,
    #                                           'department': sur_department,
    #                                           'operating_room': sur_room,
    #                                           'services': ser,
    #                                           'pathology': self.pathology.id,
    #                                           'patient': self.patient.id,
    #                                           'surgery_date': datetime.datetime.now(),
    #                                           'surgeon': self.doctor.id,
    #                                           'walkin': self._origin.id,
    #                                           'state': 'Draft'}))
    #         else:
    #             spec_department = ser.service_department.filtered(
    #                 lambda s: s.institution == self.institution and s.type == 'Specialty')
    #             spec_room = ser.service_room.filtered(lambda s: s.institution == self.institution)
    #             if spec_room:
    #                 spec_room = spec_room[0]
    #             if ser.id not in id_specialty_test_wakin:
    #                 specialty_wakin.append((0, 0, {
    #                                           'institution': self.institution.id,
    #                                           'department': spec_department,
    #                                           'perform_room': spec_room,
    #                                           'services': ser,
    #                                           'pathology': self.pathology.id,
    #                                           'patient': self.patient.id,
    #                                           'services_date': datetime.datetime.now(),
    #                                           'physician': self.doctor.id,
    #                                           'walkin': self._origin.id,
    #                                           'state': 'Draft'}))
    #         #nếu dịch vụ có đơn thuốc kèm theo
    #         # if ser.prescription_ids:
    #         #     # location_id = self.env['stock.location'].search()
    #         #     prescription_wakin.append((0, 0, {
    #         #         'info': ser.name,
    #         #         'patient': self.patient.id,
    #         #         'date': datetime.datetime.now(),
    #         #         'doctor': self.doctor.id,
    #         #         'walkin': self._origin.id,
    #         #         'state': 'Draft'}))
    #         #
    #         # print(prescription_wakin)
    #
    #     # set nguoi chi dinh khi thay doi dich vu
    #     self.update({'lab_test_ids': lab_test_wakin,'imaging_ids': img_test_wakin,'surgeries_ids': surgery_wakin,'specialty_ids':specialty_wakin})
    #     # self.update({'material_ids': marterial_wakin,'lab_test_ids': lab_test_wakin,'imaging_ids': img_test_wakin,'surgeries_ids': surgery_wakin,'taskmaster': self.env.user.id})

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.appointment.register.walkin')
        vals['name'] = sequence
        res = super(SHealthAppointmentWalkin, self).create(vals)

        # log access patient
        vals_log = {'walkin': res.id,
                    'patient': res.patient.id,
                    'department': res.department.id,
                    'date_in': res.date}
        self.env['sh.medical.patient.log'].create(vals_log)
        return res

    @api.onchange('patient')
    def onchange_patient(self):
        if self.patient:
            self.dob = self.patient.dob
            self.sex = self.patient.sex
            self.marital_status = self.patient.marital_status
            self.blood_type = self.patient.blood_type
            self.rh = self.patient.rh

    @api.multi
    def _default_account(self):
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        return journal.default_credit_account_id.id

    # @api.multi
    # def action_walkin_invoice_create(self):
    #     invoice_obj = self.env["account.invoice"]
    #     invoice_line_obj = self.env["account.invoice.line"]
    #     inv_ids = []
    #
    #     for acc in self:
    #         # Create Invoice
    #         if acc.doctor:
    #             curr_invoice = {
    #                 'partner_id': acc.patient.partner_id.id,
    #                 'account_id': acc.patient.partner_id.property_account_receivable_id.id,
    #                 'patient': acc.patient.id,
    #                 'state': 'draft',
    #                 'type':'out_invoice',
    #                 'date_invoice': acc.date.date(),
    #                 'origin': "Walkin # : " + acc.name,
    #             }
    #
    #             inv_ids = invoice_obj.create(curr_invoice)
    #
    #             if inv_ids:
    #                 inv_id = inv_ids.id
    #                 prd_account_id = self._default_account()
    #
    #                 # Create Invoice line
    #                 curr_invoice_line = {
    #                     'name':"Consultancy invoice for " + acc.name,
    #                     'price_unit': acc.doctor.consultancy_price,
    #                     'quantity': 1,
    #                     'account_id': prd_account_id,
    #                     'invoice_id': inv_id,
    #                 }
    #
    #                 inv_line_ids = invoice_line_obj.create(curr_invoice_line)
    #             self.write({'state': 'Invoiced'})
    #
    #         else:
    #             raise UserError(_('Configuration error!\nCould not find any physician to create the invoice !'))
    #
    #     return {
    #             'domain': "[('id','=', " + str(inv_id) + ")]",
    #             'name': 'Walkin Invoice',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             'res_model': 'account.invoice',
    #             'type': 'ir.actions.act_window'
    #     }

    @api.multi
    def update_walkin_material(self):
        # print('Cập nhật vật tư')
        self.material_ids = False

        mats = []
        seq_mat = 0
        over = False
        # for evaluation in self.evaluation_ids:
        #     for evaluation_mats in evaluation.material_ids:
        #         seq_mat += 1
        #         if evaluation.evaluation_type == 'Inpatient Admission':  # nếu loại đánh giá là nhập viện thì lấy vật tư ở khoa hậu phẫu
        #             dept = self.env['sh.medical.health.center.ward'].search(
        #                 [('institution', '=', self.institution.id), ('type', '=', 'Inpatient')], limit=1)
        #             evaluation_dept = dept.id
        #             evaluation_inst = self.institution.id
        #             note = "Inpatient"
        #         else:  # nếu là loại đánh giá khác thì trừ vtth ở khoa theo phiếu đánh giá
        #             evaluation_dept = self.department.id
        #             evaluation_inst = self.institution.id
        #             note = "Evaluation"
        #
        #         mats.append((0, 0, {'product_id': evaluation_mats.supply.id,
        #                                 'sequence': seq_mat,
        #                                 'init_quantity': evaluation_mats.qty,
        #                                 'quantity': evaluation_mats.qty_used,
        #                                 'institution': evaluation_inst,
        #                                 'department': evaluation_dept,
        #                                 'uom_id': evaluation_mats.uom_id.id,
        #                                 'is_readonly': True,
        #                                 'note': note,
        #                                 'interner_note': note}))
        #         over = True

        id_marterial_lab = {}
        for lab in self.lab_test_ids.filtered(lambda l: l.state == 'Completed'):
            for lab_mats in lab.lab_test_material_ids:
                # chuyen doi ve đon vi goc cua medicament
                lab_dict_key = str(lab_mats.product_id.id) + '-' + str(lab.department.id) + '-' + 'Labtest' + '-' + str(
                    lab.perform_room.location_supply_stock.id)
                lab_qty_line = lab_mats.uom_id._compute_quantity(lab_mats.quantity, lab_mats.product_id.uom_id)
                lab_init_qty_line = lab_mats.uom_id._compute_quantity(lab_mats.init_quantity,
                                                                      lab_mats.product_id.uom_id)

                # chua co thi tao moi
                if not id_marterial_lab.get(lab_dict_key):
                    seq_mat += 1
                    id_marterial_lab[lab_dict_key] = seq_mat

                    mats.append((0, 0, {'product_id': lab_mats.product_id.id,
                                        'sequence': seq_mat,
                                        'init_quantity': lab_init_qty_line,
                                        'quantity': lab_qty_line,
                                        'institution': lab.institution.id,
                                        'department': lab.department.id,
                                        'uom_id': lab_mats.product_id.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Labtest',
                                        'location_id': lab.perform_room.location_supply_stock.id,
                                        'interner_note': lab.perform_room.location_supply_stock.name if lab.perform_room.location_supply_stock.name else lab.perform_room.name}))
                # co vtth roi thi cộng dồn số yc ban đầu và số lượng sử dụng
                else:
                    mats[id_marterial_lab[lab_dict_key] - 1][2]['init_quantity'] += lab_init_qty_line
                    mats[id_marterial_lab[lab_dict_key] - 1][2]['quantity'] += lab_qty_line

                if mats[id_marterial_lab[lab_dict_key] - 1][2]['quantity'] > \
                        mats[id_marterial_lab[lab_dict_key] - 1][2]['init_quantity']:
                    over = True

        id_marterial_img = {}
        for img in self.imaging_ids.filtered(lambda i: i.state == 'Completed'):
            for img_mats in img.imaging_material_ids:
                # chuyen doi ve đon vi goc cua medicament
                img_dict_key = str(img_mats.product_id.id) + '-' + str(img.department.id) + '-' + 'Imaging' + '-' + str(
                    img.perform_room.location_supply_stock.id)
                img_qty_line = img_mats.uom_id._compute_quantity(img_mats.quantity, img_mats.product_id.uom_id)
                img_init_qty_line = img_mats.uom_id._compute_quantity(img_mats.init_quantity,
                                                                      img_mats.product_id.uom_id)
                # chua co thi tao moi
                if not id_marterial_img.get(img_dict_key):
                    seq_mat += 1
                    id_marterial_img[img_dict_key] = seq_mat
                    mats.append((0, 0, {'product_id': img_mats.product_id.id,
                                        'sequence': seq_mat,
                                        'init_quantity': img_init_qty_line,
                                        'quantity': img_qty_line,
                                        'institution': img.institution.id,
                                        'department': img.department.id,
                                        'uom_id': img_mats.product_id.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Imaging',
                                        'location_id': img.perform_room.location_supply_stock.id,
                                        'interner_note': img.perform_room.location_supply_stock.name if img.perform_room.location_supply_stock.name else img.perform_room.name}))

                # co vtth roi thi cộng dồn số yc ban đầu và số lượng sử dụng
                else:
                    mats[id_marterial_img[img_dict_key] - 1][2]['init_quantity'] += img_init_qty_line
                    mats[id_marterial_img[img_dict_key] - 1][2]['quantity'] += img_qty_line

                if mats[id_marterial_img[img_dict_key] - 1][2]['quantity'] > \
                        mats[id_marterial_img[img_dict_key] - 1][2]['init_quantity']:
                    over = True

        id_marterial_sur = {}
        for sur in self.surgeries_ids.filtered(lambda s: s.state in ['Done', 'Signed']):
            for sur_mats in sur.supplies:
                # chuyen doi ve đon vi goc cua medicament
                sur_dict_key = str(sur_mats.supply.id) + '-' + str(
                    sur.department.id) + '-' + 'Surgery' + '-' + str(
                    sur_mats.location_id)
                sur_qty_line = sur_mats.uom_id._compute_quantity(sur_mats.qty_used, sur_mats.supply.uom_id)
                sur_init_qty_line = sur_mats.uom_id._compute_quantity(sur_mats.qty,
                                                                      sur_mats.supply.uom_id)
                # chua co thi tao moi
                if not id_marterial_sur.get(sur_dict_key):
                    seq_mat += 1
                    id_marterial_sur[sur_dict_key] = seq_mat
                    mats.append((0, 0, {'product_id': sur_mats.supply.id,
                                        'sequence': seq_mat,
                                        'init_quantity': sur_init_qty_line,
                                        'quantity': sur_qty_line,
                                        'institution': sur.institution.id,
                                        'department': sur.department.id,
                                        'uom_id': sur_mats.supply.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Surgery',
                                        'location_id': sur_mats.location_id.id,
                                        'interner_note': sur_mats.location_id.name}))
                # co vtth roi thi cộng dồn số yc ban đầu và số lượng sử dụng
                else:
                    mats[id_marterial_sur[sur_dict_key] - 1][2]['init_quantity'] += sur_init_qty_line
                    mats[id_marterial_sur[sur_dict_key] - 1][2]['quantity'] += sur_qty_line

                if mats[id_marterial_sur[sur_dict_key] - 1][2]['quantity'] > \
                        mats[id_marterial_sur[sur_dict_key] - 1][2]['init_quantity']:
                    over = True

        id_marterial_spec = {}
        for spec in self.specialty_ids.filtered(lambda sp: sp.state in ['Done']):
            for spec_mats in spec.supplies:
                # chuyen doi ve đon vi goc cua medicament
                spec_dict_key = str(spec_mats.supply.id) + '-' + str(
                    spec.department.id) + '-' + 'Specialty' + '-' + str(
                    spec_mats.location_id)
                spec_qty_line = spec_mats.uom_id._compute_quantity(spec_mats.qty_used, spec_mats.supply.uom_id)
                spec_init_qty_line = spec_mats.uom_id._compute_quantity(spec_mats.qty,
                                                                        spec_mats.supply.uom_id)
                # chua co thi tao moi
                if not id_marterial_spec.get(spec_dict_key):
                    seq_mat += 1
                    id_marterial_spec[spec_dict_key] = seq_mat
                    mats.append((0, 0, {'product_id': spec_mats.supply.id,
                                        'sequence': seq_mat,
                                        'init_quantity': spec_mats.qty,
                                        'quantity': spec_mats.qty_used,
                                        'institution': spec.institution.id,
                                        'department': spec.department.id,
                                        'uom_id': spec_mats.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Specialty',
                                        'location_id': spec_mats.location_id.id,
                                        'interner_note': spec_mats.location_id.name}))

                # co vtth roi thi cộng dồn số yc ban đầu và số lượng sử dụng
                else:
                    mats[id_marterial_spec[spec_dict_key] - 1][2]['init_quantity'] += spec_init_qty_line
                    mats[id_marterial_spec[spec_dict_key] - 1][2]['quantity'] += spec_qty_line

                if mats[id_marterial_spec[spec_dict_key] - 1][2]['quantity'] > \
                        mats[id_marterial_spec[spec_dict_key] - 1][2]['init_quantity']:
                    over = True

        id_marterial_rouding = {}
        id_marterial_instruction = {}
        for inpatient in self.inpatient_ids:
            # CHI TIET DIEU DUONG
            for rounding in inpatient.roundings:
                # ghi nhận VTTH - CSHP
                for rounding_mat in rounding.medicaments:
                    # TINH TOAN SO LUONG VAT TU BAN DAU
                    # for ser in self.service:
                    #     # add vat tu tieu hao tong - ban dau
                    #     for df_mats in ser.material_ids:
                    #         if df_mats.note == 'Inpatient':
                    #             walkin_dict_key = str(df_mats.product_id.id) + '-' + str(df_mats.note)
                    #             if not id_marterial_hp.get(walkin_dict_key):
                    #                 seq_mat += 1
                    #                 id_marterial_hp[walkin_dict_key] = seq_mat
                    #                 marterial_hp[str(df_mats.product_id.id)] = df_mats.quantity
                    #             #co vtth roi thi lay so luong lon nhat
                    #             elif df_mats.quantity > marterial_hp[str(df_mats.product_id.id)]:
                    #                 marterial_hp[str(df_mats.product_id.id)] = df_mats.quantity

                    # chuyen doi ve đon vi goc cua medicament
                    rounding_dict_key = str(rounding_mat.medicine.id) + '-' + str(
                        inpatient.bed.room.location_supply_stock.id) + '-' + 'Inpatient' + '-' + str(
                        rounding_mat.location_id)
                    rounding_qty_line = rounding_mat.uom_id._compute_quantity(rounding_mat.qty,
                                                                              rounding_mat.medicine.uom_id)

                    # chua co thi tao moi
                    if not id_marterial_rouding.get(rounding_dict_key):
                        seq_mat += 1
                        id_marterial_rouding[rounding_dict_key] = seq_mat
                        mats.append((0, 0, {'product_id': rounding_mat.medicine.id,
                                            'sequence': seq_mat,
                                            'init_quantity': 0,
                                            'quantity': rounding_qty_line,
                                            'institution': self.institution.id,
                                            'department': inpatient.bed.ward.id,
                                            'uom_id': rounding_mat.medicine.uom_id.id,
                                            'is_readonly': True,
                                            'note': 'Inpatient',
                                            'location_id': rounding_mat.location_id.id,
                                            'interner_note': rounding_mat.location_id.name}))
                    # co vtth roi thi cộng dồn số lượng sử dụng
                    else:
                        mats[id_marterial_rouding[rounding_dict_key] - 1][2]['quantity'] += rounding_qty_line

            # Y LENH
            for instruction in inpatient.instructions:
                for ylhp_mat in instruction.ins_medicaments:
                    # ghi nhận THUOC - CSHP
                    instruction_dict_key = str(ylhp_mat.medicine.id) + '-' + str(
                        inpatient.bed.room.location_medicine_stock.id) + '-' + 'Inpatient' + '-' + str(
                        ylhp_mat.location_id)
                    instruction_qty_line = ylhp_mat.uom_id._compute_quantity(ylhp_mat.qty,
                                                                             ylhp_mat.medicine.uom_id)
                    # chua co thi tao moi
                    if not id_marterial_instruction.get(instruction_dict_key):
                        seq_mat += 1
                        id_marterial_instruction[instruction_dict_key] = seq_mat
                        mats.append((0, 0, {'product_id': ylhp_mat.medicine.id,
                                            'sequence': seq_mat,
                                            'init_quantity': 0,
                                            'quantity': instruction_qty_line,
                                            'institution': self.institution.id,
                                            'department': inpatient.bed.ward.id,
                                            'uom_id': ylhp_mat.medicine.uom_id.id,
                                            'is_readonly': True,
                                            'note': 'Inpatient',
                                            'location_id': ylhp_mat.location_id.id,
                                            'interner_note': ylhp_mat.location_id.name}))
                    # co vtth roi thi cộng dồn số lượng sử dụng
                    else:
                        mats[id_marterial_instruction[instruction_dict_key] - 1][2]['quantity'] += instruction_qty_line

        # VTTH THUOC CAP CHO BENH NHAN SAU DICH VU
        id_medicine_line = {}
        # check đã có thì cộng dồn
        for prescription in self.prescription_ids:
            for medicine in prescription.prescription_line:
                med_dict_key = str(medicine.name.id) + '-' + 'Medicine'
                med_init_qty_line = medicine.dose_unit_related._compute_quantity(medicine.init_qty,
                                                                                 medicine.name.uom_id)
                med_qty_line = medicine.dose_unit_related._compute_quantity(medicine.qty,
                                                                            medicine.name.uom_id)

                if medicine.name.id not in id_medicine_line:
                    seq_mat += 1
                    id_medicine_line[med_dict_key] = seq_mat
                    mats.append((0, 0, {'product_id': medicine.name.id,
                                        'sequence': seq_mat,
                                        'init_quantity': med_init_qty_line,
                                        'quantity': med_qty_line,
                                        'institution': self.institution.id,
                                        'department': self.service[0].service_department.filtered(
                                            lambda s: s.institution == self.institution)[0].id if self.service[
                                            0].service_department else 1,
                                        'uom_id': medicine.name.uom_id.id,
                                        'is_readonly': True,
                                        'note': 'Medicine',
                                        'location_id': prescription.location_id.id,
                                        'interner_note': prescription.location_id.name}))
                else:
                    mats[id_medicine_line[med_dict_key] - 1][2]['init_quantity'] += med_init_qty_line
                    mats[id_medicine_line[med_dict_key] - 1][2]['quantity'] += med_qty_line

                if mats[id_medicine_line[med_dict_key] - 1][2]['quantity'] > \
                        mats[id_medicine_line[med_dict_key] - 1][2]['init_quantity']:
                    over = True

        # chua co nguoi duyet phieu
        if not self.user_approval:
            self.write({'material_ids': mats, 'is_over_material': over})
        else:
            self.write({'material_ids': mats})

        # view_id = self.env.ref('shealth_all_in_one.sh_medical_materials_of_walkin_tree').id
        # return {'type': 'ir.actions.act_window',
        #         'name': _('Materials of Walkin Details'),
        #         'res_model': 'sh.medical.walkin.material',
        #         'target': 'new',
        #         'view_mode': 'tree,form',
        #         'domain': [('walkin','=',self.id)],
        #         'views': [[view_id, 'tree']],
        #         }

    # @api.multi
    # def view_walkin_material_over(self):
    #     view_id = self.env.ref('shealth_all_in_one.sh_medical_register_for_walkin_over_tree').id
    #     return {'type': 'ir.actions.act_window',
    #             'name': _('Materials of Walkin Details'),
    #             'res_model': 'sh.medical.walkin.material',
    #             'target': 'new',
    #             'view_type': 'tree',
    #             # 'search_view_id ': self.env.ref('shealth_all_in_one.view_sh_medical_walkin_material_filter').id,
    #             'domain': [('walkin', '=', self.id)],
    #             # 'context': {'search_default_group_department': True},
    #             'views': [[view_id, 'tree']],
    #             }

    @api.multi
    def set_to_completed(self):
        lab_test_ids = fields.One2many('sh.medical.lab.test', 'walkin', string='Lab Tests', readonly=False,
                                       states={'Completed': [('readonly', True)]})
        imaging_ids = fields.One2many('sh.medical.imaging', 'walkin', string='Imaging Tests', readonly=False,
                                      states={'Completed': [('readonly', True)]})
        surgeries_ids = fields.One2many('sh.medical.surgery', 'walkin', string='Surgeries Tests', readonly=False,
                                        states={'Completed': [('readonly', True)]})
        specialty_ids = fields.One2many('sh.medical.specialty', 'walkin', string='Specialty Tests', readonly=False,
                                        states={'Completed': [('readonly', True)]})

        # còn phiếu xn
        if len(self.lab_test_ids.filtered(lambda lt: lt.state not in ["Completed"])) > 0:
            raise UserError(_('Bạn không thể đóng phiếu khi có phiếu xét nghiệm chưa được xác nhận hoàn thành!'))
        # còn phiếu cđha
        if len(self.imaging_ids.filtered(lambda lt: lt.state not in ["Completed"])) > 0:
            raise UserError(
                _('Bạn không thể đóng phiếu khi có phiếu Chuẩn đoan hình ảnh - Thăm dò chức năng được xác nhận hoàn thành!'))
        # còn phiếu pttt
        if len(self.surgeries_ids.filtered(lambda lt: lt.state not in ["Done", "Signed"])) > 0:
            raise UserError(
                _('Bạn không thể đóng phiếu khi có phiếu Phẫu thuật thủ thuật chưa được xác nhận hoàn thành!'))

        # còn phiếu chuyên khoa
        if len(self.specialty_ids.filtered(lambda lt: lt.state not in ["Done"])) > 0:
            raise UserError(_('Bạn không thể đóng phiếu khi có phiếu chuyên khoa chưa được xác nhận hoàn thành!'))

        # còn đơn thuốc
        if len(self.prescription_ids.filtered(lambda ints: ints.state == "Draft")) > 0:
            raise UserError(_('Bạn không thể đóng phiếu khi có đơn thuốc chưa được xác nhận xuất!'))

        # còn phiếu nhập viên
        if len(self.inpatient_ids.filtered(lambda ints1: ints1.state not in ["Discharged", "Cancelled"])) > 0:
            raise UserError(_('Bạn không thể đóng phiếu lưu bệnh nhân chưa được xác nhận đã kết thúc chăm sóc!'))

        # cap nhat vat tu cho phieu kham
        self.update_walkin_material()

        self.handle = self.handle if self.handle else 'discharge'
        self.date_out = self.date_out if self.date_out else datetime.datetime.now()

        return self.write({'state': 'Completed'})  # cap nhat trang thai phieu kham

    @api.multi
    def set_to_wait_payment(self):
        return self.write({'state': 'WaitPayment'})

    @api.multi
    def set_to_progress(self):
        lab_test_wakin = []
        id_lab_test_wakin = self.lab_test_ids.mapped('test_type').ids

        img_test_wakin = []
        id_img_test_wakin = self.imaging_ids.mapped('test_type').ids

        surgery_wakin = []
        id_surgery_test_wakin = self.surgeries_ids.mapped('services').ids

        specialty_wakin = []
        id_specialty_test_wakin = self.specialty_ids.mapped('services').ids

        # TAO CÁC PHIEU XN, CĐHA, PTTT, CK NẾU CÓ
        seq_mat = 0
        for ser in self.sudo().service:
            # add lab test
            for lab in ser.lab_type_ids:
                if lab.id not in id_lab_test_wakin:
                    lab_department = self.env['sh.medical.health.center.ward'].search(
                        [('institution', '=', self.institution.id), ('type', '=', 'Laboratory')], limit=1)

                    # ghi nhận case xn và vtth nếu có
                    lt_data = []
                    seq = 0
                    for lt in lab.material_ids:
                        seq += 1
                        lt_data.append((0, 0, {'sequence': seq,
                                               'product_id': lt.product_id.id,
                                               'init_quantity': lt.quantity,
                                               'quantity': lt.quantity,
                                               'is_init': True,
                                               'uom_id': lt.uom_id.id}))
                    lt_case_data = []
                    seq_case = 0
                    for lt_case in lab.lab_criteria:
                        seq_case += 1
                        lt_case_data.append((0, 0, {'sequence': seq_case,
                                                    'name': lt_case.name,
                                                    'normal_range': lt_case.normal_range,
                                                    'units': lt_case.units.id}))

                    id_lab_test_wakin.append(lab.id)  # co roi se khong add thêm nữa
                    lab_test_wakin.append((0, 0, {
                        'institution': self.institution.id,
                        'department': lab_department.id,
                        'test_type': lab.id,
                        'perform_room': False if self.env.ref('shealth_all_in_one.sh_labtest_room_knhn',
                                                              False) == None else self.env.ref(
                            'shealth_all_in_one.sh_labtest_room_knhn').id,
                        'has_child': lab.has_child,
                        'normal_range': lab.normal_range,
                        'patient': self.patient.id,
                        'pathologist': self.env.ref('__import__.data_physician_2').id if self.env.ref(
                            '__import__.data_physician_2', False) else False,
                        'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                     "%Y-%m-%d %H:%M:%S") + timedelta(
                            minutes=15) or fields.Datetime.now(),
                        'date_analysis': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                    "%Y-%m-%d %H:%M:%S") + timedelta(
                            minutes=30) or fields.Datetime.now(),
                        'date_done': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                "%Y-%m-%d %H:%M:%S") + timedelta(
                            hours=2) or fields.Datetime.now(),
                        'requestor': self.doctor.id,
                        'lab_test_material_ids': lt_data,
                        'lab_test_criteria': lt_case_data,
                        'walkin': self.id,
                        'state': 'Draft'}))

            # add imaging test
            for img in ser.imaging_type_ids:
                if img.id not in id_img_test_wakin:
                    img_department = self.env['sh.medical.health.center.ward'].search(
                        # [('institution', '=', self.institution.id), ('type', '=', 'Imaging')], limit=1)
                        [('institution', '=', self.institution.id), ('type', '=', 'Laboratory')], limit=1)

                    # ghi nhận vtth nếu có
                    img_data = []
                    seq = 0
                    for ir in img.material_ids:
                        seq += 1
                        img_data.append((0, 0, {'sequence': seq,
                                                'product_id': ir.product_id.id,
                                                'init_quantity': ir.quantity,
                                                'quantity': ir.quantity,
                                                'is_init': True,
                                                'uom_id': ir.uom_id.id}))

                    id_img_test_wakin.append(img.id)  # co roi se khong add thêm nữa
                    # print(img.perform_room)
                    img_test_wakin.append((0, 0, {
                        'institution': self.institution.id,
                        'department': img_department.id,
                        'test_type': img.id,
                        'perform_room': img.perform_room.id if img.perform_room else False,
                        'patient': self.patient.id,
                        'pathologist': self.env.ref('__import__.data_physician_canlamsang').id if self.env.ref(
                            '__import__.data_physician_canlamsang', False) else False,
                        'date_requested': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                     "%Y-%m-%d %H:%M:%S") + timedelta(
                            minutes=15) or fields.Datetime.now(),
                        'date_analysis': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                    "%Y-%m-%d %H:%M:%S") + timedelta(
                            minutes=30) or fields.Datetime.now(),
                        'date_done': datetime.datetime.strptime(self.date.strftime("%Y-%m-%d %H:%M:%S"),
                                                                "%Y-%m-%d %H:%M:%S") + timedelta(
                            hours=2) or fields.Datetime.now(),
                        'requestor': self.doctor.id,
                        'imaging_material_ids': img_data,
                        'walkin': self.id,
                        'state': 'Draft'}))

        # neu là dich vu khoa phau thuat
        if self.flag_surgery:
            sur_department = self.env['sh.medical.health.center.ward'].search(
                [('institution', '=', self.institution.id), ('type', '=', 'Surgery')], limit=1)

            major_surgery_list = self.sudo().service.filtered(lambda s: s.surgery_type == 'major')
            # nếu trong dịch vụ phát sinh có dịch vụ đại phẫu => tất cả dịch vụ dc thực hiện ở phòng đại phẫu ko thì thực hiện ở tiểu phẫu
            room_minor = False if self.env.ref('shealth_all_in_one.sh_supersonic_tieuphau_room_knhn',
                                               False) == None else self.env.ref(
                'shealth_all_in_one.sh_supersonic_tieuphau_room_knhn').id
            room_major = False if self.env.ref('shealth_all_in_one.sh_supersonic_daiphau_room_knhn',
                                               False) == None else self.env.ref(
                'shealth_all_in_one.sh_supersonic_daiphau_room_knhn').id

            sur_room = room_major if len(major_surgery_list) > 0 else room_minor
            anesthetist_type = 'me' if len(major_surgery_list) > 0 else 'te'
            surgery_wakin.append((0, 0, {
                'institution': self.institution.id,
                'department': sur_department.id,
                'operating_room': sur_room,
                'services': [(6, 0, self.sudo().service.ids)],
                'pathology': [(6, 0, self.sudo().pathology.ids)],
                'anesthetist_type': anesthetist_type,
                'surgical_diagram': ' '.join(map(str, self.sudo().service.mapped('surgical_diagram'))),
                'surgical_order': ' '.join(map(str, self.sudo().service.mapped('surgical_order'))),
                'patient': self.patient.id,
                'date_requested': self.date,
                'surgery_date': self.date,
                'surgery_end_date': self.date,
                'surgeon': self.env.ref('__import__.data_physician_pttm').id if self.env.ref(
                    '__import__.data_physician_pttm', False) else False,
                'anesthetist': self.env.ref('__import__.data_physician_gmhs').id if self.env.ref(
                    '__import__.data_physician_gmhs', False) else False,
                'walkin': self.id,
                'state': 'Draft'}))
        else:
            spec_department = \
            self.sudo().service[0].service_department.filtered(lambda s: s.institution == self.institution)[0].id if \
            self.sudo().service[0].service_department else False
            spec_room = self.sudo().service[0].service_room.filtered(lambda s: s.institution == self.institution)[
                0].id if self.sudo().service[0].service_room else False

            if spec_department and \
                    self.sudo().service[0].service_department.filtered(lambda s: s.institution == self.institution)[
                        0].get_external_id() == 'shealth_all_in_onesh_dalieu_dep_knhn':
                physician_ck = self.env.ref('__import__.data_physician_dalieu').id if self.env.ref(
                    '__import__.data_physician_dalieu', False) else False
            else:
                physician_ck = self.env.ref('__import__.data_physician_rhm').id if self.env.ref(
                    '__import__.data_physician_rhm', False) else False

            specialty_wakin.append((0, 0, {
                'institution': self.institution.id,
                'department': spec_department,
                'perform_room': spec_room,
                'services': [(6, 0, self.sudo().service.ids)],
                'pathology': [(6, 0, self.sudo().pathology.ids)],
                'patient': self.patient.id,
                'date_requested': self.date,
                'services_date': self.date,
                'services_end_date': self.date,
                'physician': physician_ck,
                'walkin': self.id,
                'state': 'Draft'}))

        return self.sudo().write({'state': 'InProgress', 'lab_test_ids': lab_test_wakin, 'imaging_ids': img_test_wakin,
                                  'surgeries_ids': surgery_wakin, 'specialty_ids': specialty_wakin})

    @api.multi
    def set_to_progress_admin(self):
        # mở lại trạng thái phiếu
        return self.write({'state': 'InProgress'})

    @api.multi
    def set_to_scheduled(self):
        # draft cac phieu lab, imaging, surgeries lien quan cua phieu kham
        # for lab in self.lab_test_ids:
        #     LabTest = self.env['sh.medical.lab.test'].browse(lab.id)
        #     if LabTest.state == 'Cancelled':
        #         LabTest.write({'state': 'Draft'})
        #
        # for imaging in self.imaging_ids:
        #     ImagingTest = self.env['sh.medical.imaging'].browse(imaging.id)
        #     if ImagingTest.state == 'Cancelled':
        #         ImagingTest.write({'state': 'Draft'})
        #
        # for surgery in self.surgeries_ids:
        #     Surgery = self.env['sh.medical.surgery'].browse(surgery.id)
        #     if Surgery.state == 'Cancelled':
        #         Surgery.write({'state': 'Draft'})

        return self.write({'state': 'Scheduled'})

    # @api.multi
    # def set_to_cancelled(self):
    #     #cancel cac phieu lab, imaging, surgeries lien quan cua phieu kham
    #     for lab in self.lab_test_ids:
    #         LabTest = self.env['sh.medical.lab.test'].browse(lab.id)
    #         if LabTest.state == 'Draft':
    #             LabTest.write({'state': 'Cancelled'})
    #
    #     for imaging in self.imaging_ids:
    #         ImagingTest = self.env['sh.medical.imaging'].browse(imaging.id)
    #         if ImagingTest.state == 'Draft':
    #             ImagingTest.write({'state': 'Cancelled'})
    #
    #     for surgery in self.surgeries_ids:
    #         Surgery = self.env['sh.medical.surgery'].browse(surgery.id)
    #         if Surgery.state == 'Draft':
    #             Surgery.write({'state': 'Cancelled'})
    #
    #     return self.write({'state': 'Cancelled'})

    @api.multi
    def create_draft_payment(self):
        if self.service:
            service_name = ''
            total = 0
            for ser in self.service:
                total += ser.list_price
                service_name += ser.name + ": " + "{:,.0f}đ".format(ser.list_price) + ";"

            self.env['account.payment'].create({
                'partner_id': self.patient.partner_id.id,
                'patient': self.patient.id,
                'company_id': self.patient.company_id.id,
                'currency_id': self.patient.currency_id.id,
                'amount': total,
                'note': "Thu tiền dịch vụ: " + service_name,
                'text_total': num2words_vnm(int(total)) + " đồng",
                'partner_type': 'customer',
                'payment_type': 'inbound',
                'payment_date': self.date.strftime("%Y-%m-%d"),  # ngày thanh toán
                'date_requested': self.date.strftime("%Y-%m-%d"),  # ngày yêu cầu
                'payment_method_id': '1',
                'journal_id': 7,
                'walkin': self.id,
                'user': self.institution.user_payment.id,
            })
            return self.write({'state': 'WaitPayment'})
        else:
            raise ValidationError(_('You must select at least one service!'))

    @api.multi
    def unlink(self):
        for walkin in self.filtered(lambda walkin: walkin.state not in ['Scheduled']):
            raise UserError(_('You can not delete a walkin record that is not in "Scheduled" stage !!'))
        return super(SHealthAppointmentWalkin, self).unlink()

    # This function prints the assign lab test
    @api.multi
    def print_assign_patient_labtest(self):
        return self.env.ref('shealth_all_in_one.action_report_assign_patient_labtest').report_action(self)

    # This function prints the result lab test
    @api.multi
    def print_result_patient_labtest(self):
        return self.env.ref('shealth_all_in_one.action_report_result_patient_labtest').report_action(self)

    # This function prints the assign img test
    @api.multi
    def print_assign_patient_imaging(self):
        return self.env.ref('shealth_all_in_one.action_report_assign_patient_imaging_multi').report_action(self)

    # This function prints the result img test
    @api.multi
    def print_result_patient_imaging(self):
        return self.env.ref('shealth_all_in_one.action_result_result_patient_imaging').report_action(self)

    # This function prints the assign services
    @api.multi
    def print_assign_patient_services(self):
        return self.env.ref('shealth_all_in_one.action_report_assign_patient_services').report_action(self)

    def add_evaluations(self):
        institution = self.env['sh.medical.health.center'].sudo().search([], limit=1)

        res = self.env['sh.medical.evaluation'].create({
            'walkin': self.env.context.get('default_walkin'),
            'patient':  self.env.context.get('default_patient'),
            'doctor':  self.env.context.get('default_doctor'),
            'evaluation_start_date': datetime.date.today(),
            'services': self.env.context.get('default_services'),
            'institution': institution.id if institution else self.env.context.get('default_institution'),
        })
        res.write({'services': self.env.context.get('default_services')})


        # # res.write({'chief_complaint': 'Tái khám: %s' % ','.join(res.services.mapped('name')),'ward': res.walkin.service_room.related_department.id})
        res.write({'ward': res.walkin.service_room.department.id})

        return {
            'name': _('Chi tiết phiếu tái khám bệnh nhân'),  # label
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('shealth_all_in_one.sh_medical_evaluation_view').id,
            'res_model': 'sh.medical.evaluation',  # model want to display
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
            'res_id': res.id
        }

# Physician schedule management for Walkins

class SHealthPhysicianWalkinSchedule(models.Model):
    _name = "sh.medical.physician.walkin.schedule"
    _description = "Information about walkin schedule"

    name = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    physician_id = fields.Many2one('sh.medical.physician', string='Physician', index=True, ondelete='cascade')

    _order = 'name desc'


# Inheriting Physician screen to add walkin schedule lines
class SHealthPhysician(models.Model):
    _inherit = "sh.medical.physician"
    # walkin_schedule_lines = fields.One2many('sh.medical.physician.walkin.schedule', 'physician_id', string='Walkin Schedule')
    walkin = fields.One2many('sh.medical.appointment.register.walkin', 'doctor', string='Walkin Schedule')


# Inheriting Inpatient module to add "Walkin" screen reference
class shealthInpatient(models.Model):
    _inherit = 'sh.medical.inpatient'
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', ondelete='cascade')

    @api.onchange('walkin')
    def _onchange_walkin(self):
        if self.walkin:
            self.patient = self.walkin.patient
            self.admission_reason = self.walkin.pathology.ids
            self.admission_reason_walkin = self.walkin.reason_check
            self.services = self.walkin.service


# Inheriting Prescription module to add "Walkin" screen reference
class SHealthPrescription(models.Model):
    _inherit = 'sh.medical.prescription'
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', ondelete='cascade')


# Inheriting Evaluation module to add "Walkin" screen reference



# Inheriting LabTests module to add "Walkin" screen reference
class SHealthLabTests(models.Model):
    _inherit = 'sh.medical.lab.test'
    _order = "walkin"

    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', ondelete='cascade')

    # @api.model
    # def create(self, vals):
    #     if vals['test_type']:
    #         lt_data = []
    #         test_type_id = vals['test_type']
    #         test_type = self.env['sh.medical.labtest.types'].sudo().browse(test_type_id)
    #         seq = 0
    #         for lt in test_type.material_ids:
    #             seq +=1
    #             lt_data.append((0, 0, {'sequence': seq,
    #                                    'product_id': lt.product_id.id,
    #                                    'init_quantity': lt.quantity,
    #                                    'is_init': True,
    #                                    'uom_id': lt.uom_id.id}))
    #         vals['lab_test_material_ids'] = lt_data
    #
    #         lt_case_data = []
    #         test_type_id = vals['test_type']
    #         test_type = self.env['sh.medical.labtest.types'].sudo().browse(test_type_id)
    #         seq_case = 0
    #         for lt_case in test_type.lab_criteria:
    #             seq_case += 1
    #             lt_case_data.append((0, 0, {'sequence': seq_case,
    #                                    'name': lt_case.name,
    #                                    'normal_range': lt_case.normal_range,
    #                                    'units': lt_case.units.id}))
    #         vals['lab_test_criteria'] = lt_case_data
    #
    #     return super(SHealthLabTests, self).create(vals)


# Inheriting Imaging module to add "Walkin" screen reference
class SHealthImaging(models.Model):
    _inherit = 'sh.medical.imaging'

    _order = "walkin"
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', readonly=True,
                             ondelete='cascade')

    # @api.model
    # def create(self, vals):
    #     if vals['test_type']:
    #         lt_data = []
    #         test_type_id = vals['test_type']
    #         test_type = self.env['sh.medical.imaging.test.type'].sudo().browse(test_type_id)
    #         seq = 0
    #         for lt in test_type.material_ids:
    #             seq += 1
    #             lt_data.append((0, 0, {'sequence': seq,
    #                                    'product_id': lt.product_id.id,
    #                                    'init_quantity': lt.quantity,
    #                                    'is_init': True,
    #                                    'uom_id': lt.uom_id.id}))
    #         vals['imaging_material_ids'] = lt_data
    #         vals['analysis'] = test_type.analysis
    #         vals['conclusion'] = test_type.conclusion
    #
    #     return super(SHealthImaging, self).create(vals)


# Inheriting Surgeries module to add "Walkin" screen reference
class SHealthSurgery(models.Model):
    _inherit = 'sh.medical.surgery'

    _order = "walkin"
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', required=True, readonly=True,
                             ondelete='cascade')
    services_domain = fields.Many2many('sh.medical.health.center.service', related='walkin.service')
    pathology_icd9 = fields.Many2one('sh.medical.pathology.icd9', 'Mã icd9')
    # @api.model
    # def create(self, vals):
    #     res = super(SHealthSurgery, self).create(vals)

    # add vat tu tieu hao cho pttt
    # sg_data = []
    # for ser in res.services_domain:
    #     service_mats = ser.material_ids
    #     print(ser.name)
    #     for sg in service_mats:
    #         if sg.note == 'Surgery':
    #             sg_data.append((0, 0, {'note': sg.note,
    #                                    'supply': sg.product_id.id,
    #                                    'qty': sg.quantity,
    #                                    'qty_use': 0,
    #                                    'uom_id': sg.uom_id.id}))

    # sg_data = []
    # for sg in material_of_walkin:
    #     # print(sg.note)
    #     if sg.note == 'Surgery':
    #         sg_data.append((0, 0, {'note': sg.note,
    #                                'supply': sg.product_id.id,
    #                                'qty': sg.quantity,
    #                                'qty_use': sg.uom_id.id,
    #                                'uom_id': sg.uom_id.id}))
    # nhap nhom benh icd10
    # pathology = False
    # if res.walkin.pathology:
    #     pathology = res.walkin.pathology.id

    # nhap dich vu su dung
    # services_of_walkin = res.walkin.service.filtered(lambda s : s.is_surgeries == True)

    # res.update({'supplies': sg_data})
    # return res


# Inheriting Specialty module to add "Walkin" screen reference
class SHealthSpecialty(models.Model):
    _inherit = 'sh.medical.specialty'

    _order = "walkin"
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', required=True, readonly=True,
                             ondelete='cascade')
    services_domain = fields.Many2many('sh.medical.health.center.service', related='walkin.service')
    pathology_icd9 = fields.Many2one('sh.medical.pathology.icd9', 'Mã icd9')


# Inheriting vaccines module to add "Walkin" screen reference
class SHealthVaccines(models.Model):
    _inherit = 'sh.medical.vaccines'
    walkin = fields.Many2one('sh.medical.appointment.register.walkin', string='Queue #', ondelete='cascade')


# Inheriting Patient module to add "Walkin" screen reference
class SHealthPatient(models.Model):
    _inherit = 'sh.medical.patient'

    @api.multi
    def _walkin_count(self):
        sh_walkin = self.env['sh.medical.appointment.register.walkin']
        for pa in self:
            domain = [('patient', '=', pa.id)]
            walk_ids = sh_walkin.search(domain)
            walk = sh_walkin.browse(walk_ids)
            walk_count = 0
            for wk in walk:
                walk_count += 1
            pa.walkin_count = walk_count
        return True

    walkin = fields.One2many('sh.medical.appointment.register.walkin', 'patient', string='Registers of walkin')
    walkin_count = fields.Integer(compute=_walkin_count, string="Register of walkin")


# Inheriting Ward module to add "Walkin" screen reference
class SHealthWard(models.Model):
    _inherit = 'sh.medical.health.center.ward'

    walkin = fields.One2many('sh.medical.appointment.register.walkin', 'department', string='Walkin Schedule')
    count_walkin_not_completed = fields.Integer('Walkin not completed', compute="_count_walkin_not_completed")

    @api.multi
    def _count_walkin_not_completed(self):
        oe_walkin = self.env['sh.medical.appointment.register.walkin']
        for ls in self:
            domain = [('state', '!=', 'Completed'), ('department', '=', ls.id)]
            ls.count_walkin_not_completed = oe_walkin.search_count(domain)
        return True

