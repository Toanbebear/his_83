# -*- encoding: utf-8 -*-
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
import datetime

class SHealthPatientMedicalCert(models.Model):
    _name = 'sh.medical.patient.medical.cert'
    _description = 'Patient Medical Certificate Management'

    @api.multi
    def _get_duration(self):
        for obj in self:
            if obj.start_date and obj.end_date:
                start_date = datetime.datetime.strptime(obj.start_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                end_date = datetime.datetime.strptime(obj.end_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                duration = end_date - start_date
                obj.no_of_days = duration.days
        return True

    name = fields.Char(string='MC #', size=64, readonly=True, default=lambda *a: '/')
    start_date = fields.Date(string='From Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    no_of_days = fields.Integer(compute=_get_duration, string="No of Days")
    issue_date = fields.Datetime(string='DateTime MC is issued', required=True, default=lambda *a: datetime.datetime.now())
    patient = fields.Many2one('sh.medical.patient', string='Patient', help="Patient Name", required=True)
    doctor = fields.Many2one('sh.medical.physician', string='Physician', domain=[('is_pharmacist','=',False)], help="Health professional", required=True)
    institution = fields.Many2one('sh.medical.health.center', string='Institution', help="Institution where doctor works")
    reason = fields.Text(string='Reason', required=True)

    @api.model
    def create(self,vals):
        sequence = self.env['ir.sequence'].next_by_code('sh.medical.patient.medical.cert')
        vals['name'] = sequence
        return super(SHealthPatientMedicalCert, self).create(vals)


    # This function prints the patient medical cert
    @api.multi
    def print_patient_medical_cert(self):
        return self.env.ref('shealth_all_in_one.action_report_sh_medical_patient_medical_cert').report_action(self)


# Inheriting Patient module to add "Medical Certificate" screen reference
class SHealthPatient(models.Model):
    _inherit='sh.medical.patient'
    medical_cert_ids = fields.One2many('sh.medical.patient.medical.cert', 'patient', string='Medical Certificates')