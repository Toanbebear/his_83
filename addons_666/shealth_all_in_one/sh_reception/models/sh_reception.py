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
import time
import datetime
from datetime import timedelta


# Branch Management

class SHReception(models.Model):
    _name = 'sh.reception'
    _description = 'Đón tiếp'

    _rec_name = 'patient'
    _order = "reception_date desc"

    patient = fields.Many2one('sh.medical.patient', 'Bệnh nhân')
    walkin_id = fields.One2many('sh.medical.appointment.register.walkin', 'reception_id', string='Walkin')

    id_card = fields.Char('CMND/ Hộ chiếu',related="patient.id_card", store=True)
    dob = fields.Date('Ngày sinh',related="patient.dob", store=True)
    sex = fields.Selection([
        ('Male', 'Nam'),
        ('Female', 'Nữ')
    ], string='Giới tính', track_visibility='always',related="patient.sex", store=True)
    phone = fields.Char(string='Số điện thoại',related="patient.phone", store=True)
    street = fields.Char('Địa chỉ',related="patient.street", store=True)
    state_id = fields.Many2one('res.country.state','Thành phố',related="patient.state_id", store=True)
    country_id = fields.Many2one('res.country','Quốc gia',related="patient.country_id", store=True)

    user = fields.Many2one('res.users', string='Người đón tiếp', default=lambda self: self.env.uid, domain=lambda self: [("groups_id", "=", self.env.ref( "shealth_all_in_one.group_sh_medical_receptionist").id)])
    reception_date = fields.Datetime(string='Ngày đón tiếp', default=lambda self: fields.Datetime.now())
    reason = fields.Text(string='Lý do khám')
    reason_id = fields.Many2one('sh.reason', string='Lý do khám', domain="[('service_room_id', '=', service_room)]")
    advisory = fields.Many2one('sh.medical.health.center.service', string='Tư vấn', domain=lambda self: [("id", "=", self.env.ref( "shealth_all_in_one.sh_product_service_kb01").id)],
                               default=lambda self: self.env.ref('shealth_all_in_one.sh_product_service_kb01').id)
    service_room = fields.Many2one('sh.medical.health.center.ot', string='Phòng khám', domain=lambda self: [
        ('department', '=', self.env.ref('shealth_all_in_one.sh_kb_dep_knhn').id)])
    close = fields.Boolean(string='Kết thúc đón tiếp')

    @api.onchange('patient')
    def set_value_patient(self):
        if self.patient:
            self.id_card = self.patient.id_card
            self.dob = self.patient.dob
            self.sex = self.patient.sex
            self.phone = self.patient.phone
            self.street = self.patient.street
            self.state_id = self.patient.state_id.id
            self.country_id = self.patient.country_id.id

    @api.model
    def create(self, vals):
        vals['close'] = True
        res = super(SHReception, self).create(vals)
        if res.patient:
            wk = self.env['sh.medical.appointment.register.walkin'].create({
                'patient': res.patient.id,
                'date': datetime.datetime.strptime(res.reception_date.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S") + timedelta(minutes=5) or fields.Datetime.now(),
                'institution': res.env.ref('shealth_all_in_one.sh_medicines_health_center_kangnam_hn').id,
                'department': res.env.ref('shealth_all_in_one.sh_kb_dep_knhn').id,
                'service_room': res.service_room.id,
                'reason_check': res.reason_id.name,
                'specialty_exam': res.reason_id.name,
                'info_diagnosis': res.reason_id.name,
                'doctor': self.env.ref('__import__.data_physician_kb').id if self.env.ref('__import__.data_physician_kb',False) else False,
                'pathological_process': "Khách hàng thăm khám về %s có nguyện vọng cải thiện nên vào viện." % str(res.reason_id.name,),
                'dob': res.dob,
                'sex': res.sex,
                'blood_type': res.patient.blood_type,
                'marital_status': res.patient.marital_status,
                'rh': res.patient.rh,
                'reception_id': res.id,
                'weight': res.patient.weight,
                'height': res.patient.height,
                'bmi': res.patient.bmi,
            })
        return res

# Inheriting Patient module to add "Reception" screen reference
class SHealthPatient(models.Model):
    _inherit = 'sh.medical.patient'

    @api.multi
    def _reception_count(self):
        sh_reception = self.env['sh.reception'].sudo()
        for pa in self:
            domain = [('patient', '=', pa.id)]
            recept_ids = sh_reception.search(domain)
            recept = sh_reception.browse(recept_ids)
            reception_count = 0
            for rc in recept:
                reception_count += 1
            pa.reception_count = reception_count
        return True

    reception = fields.One2many('sh.reception', 'patient', string='Đón tiếp')
    reception_count = fields.Integer(compute=_reception_count, string="Số lần Đón tiếp")

