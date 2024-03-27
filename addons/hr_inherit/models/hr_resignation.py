# -*- coding: utf-8 -*-
import base64
import datetime
from datetime import datetime, date
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.http import request
from .mailmerge import MailMerge

date_format = "%Y-%m-%d"


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _description = "Resignation"

    _inherit = 'mail.thread'
    _rec_name = 'employee_id'

    def _get_employee_id(self):
        # assigning the related employee of the logged in user
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Nhân viên", default=_get_employee_id, required=True,
                                  help='Name of the employee for whom the request is creating')
    department_id = fields.Many2one('hr.department', string="Phòng ban", related='employee_id.department_id',
                                    help='Department of the employee')
    joined_date = fields.Date(string="Ngày vào làm", readonly=True,
                              help='Joining date of the employee')
    expected_revealing_date = fields.Date(string="Ngày nghỉ việc", required=True,
                                          help='Date on which he is revealing from the company')
    revealing_date = fields.Date(string="Ngày nộp đơn", default=date.today())
    # resign_confirm_date = fields.Date(string="Ngày phê duyệt", required=True, default=date.today())
    resign_confirm_date = fields.Date(string="Ngày phê duyệt")
    reason = fields.Text(string="Lý do", help='Specify reason for leaving the company')
    state = fields.Selection([('draft', 'Bản nháp'), ('approved', 'Chấp thuận'), ('cancel', 'Hủy')],
                             string='Trạng thái', default='draft')
    check_resignation = fields.Boolean(string='Công nợ nghị việc', default=False)

    type_reason = fields.Many2one('hr.resignation.reason', "Lý do")
    # reason = fields.Text('Lý do')
    job = fields.Many2one('hr.job', 'Chức vụ', related='employee_id.job_id', store=True)
    flag = fields.Boolean('Flag', default=False)

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def _compute_read_only(self):
        """ Use this function to check weather the user has the permission to change the employee"""
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if res_user.has_group('hr.group_hr_user'):
            self.read_only = True
        else:
            self.read_only = False

    @api.onchange('employee_id')
    def set_join_date(self):
        self.joined_date = self.employee_id.joining_date if self.employee_id.joining_date else ''

    # @api.model
    # def create(self, vals):
    #     # assigning the sequence for the record
    #     employee = self.env['hr.employee'].search([('id', '=', vals['employee_id'])], limit=1)
    #     if employee.user_id:
    #         user = request.env['res.users'].sudo().search([('id', '=', employee.user_id.id)], limit=1)
    #         user.update({'active': False})
    #         employee.update({'user_id': None})
    #     if vals.get('name', _('New')) == _('New'):
    #         vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')
    #     res = super(HrResignation, self).create(vals)
    #     return res

    @api.constrains('employee_id')
    def check_employee(self):
        # Checking whether the user is creating leave request of his/her own
        for rec in self:
            if not self.env.user.has_group('hr.group_hr_user'):
                if rec.employee_id.user_id.id and rec.employee_id.user_id.id != self.env.uid:
                    raise ValidationError(_('You cannot create request for other employees'))

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def check_request_existence(self):
        # Check whether any resignation request already exists
        for rec in self:
            if rec.employee_id:
                resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
                                                                         ('state', 'in', ['confirm', 'approved'])])
                if resignation_request:
                    raise ValidationError(
                        'Có một yêu cầu từ chức ở trạng thái được xác nhận hoặc phê duyệt cho nhân viên này!')

    def confirm_resignation(self):
        for rec in self:
            rec.state = 'approved'
            rec.resign_confirm_date = date.today()
            rec.employee_id.resign_date = date.today()
            rec.employee_id.reason_resign = rec.reason

    def cancel_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    def update_employee_status(self):
        resignation = self.env['hr.resignation'].search([('state', '=', 'approved'), ('flag', '!=', True)])
        contracts = self.env['hr.contract'].search(
            [('state', 'in', ('open', 'pending'))])  # ('employee_id', '=', self.employee_id.id)
        for rec in resignation:
            if rec.resign_confirm_date <= fields.Date.today() and rec.employee_id.active:
                contract = contracts.search([('employee_id', '=', rec.employee_id.id)])
                if contract:
                    contract.state = 'cancel'
                rec.employee_id.active = False
                rec.employee_id.resign_date = rec.resign_confirm_date
                rec.employee_id.reason_resign = rec.reason
                rec.flag = True

    def print_decision(self):
        if self.env.user.company_id.name == 'Công ty TNHH BVTM Kangnam Sài Gòn':
            decision_attachment = self.env.ref('hr_inherit.qd_nghi_viec_knsg')
        elif self.env.user.company_id.name == 'Công ty TNHH Bệnh viện thẩm mỹ Đông Á':
            decision_attachment = self.env.ref('hr_inherit.qd_nghi_viec_bvda')
        elif self.env.user.company_id.name == 'BỆNH VIỆN RĂNG HÀM MẶT THẨM MỸ PARIS':
            decision_attachment = self.env.ref('hr_inherit.qd_nghi_viec_bvrhm')
        else:
            raise ValidationError('Chưa có mẫu hợp đồng dành cho chi nhánh của bạn.')
        decode = base64.b64decode(decision_attachment.datas)
        doc = MailMerge(BytesIO(decode))
        data_list = []
        record_data = {}
        record_data['nhan_vien'] = self.employee_id.name
        record_data['ngay_nghi_text'] = self.expected_revealing_date.strftime(
            'ngày %d tháng %m năm %Y') if self.expected_revealing_date else ''
        record_data['ngay_sinh'] = self.employee_id.birthday
        record_data['cmnd'] = self.employee_id.identification_id
        record_data['chuc_vu'] = self.employee_id.job_id.name or False

        data_list.append(record_data)
        doc.merge_templates(data_list, separator='page_break')

        fp = BytesIO()
        doc.write(fp)
        doc.close()
        fp.seek(0)
        report = base64.encodebytes((fp.read()))
        fp.close()
        attachment = self.env['ir.attachment'].sudo().create({'name': 'quyet_dinh_nghi_viec %s.docx' % self.employee_id.name,
                                                              'datas': report,
                                                              'res_model': 'temp.creation',
                                                              'public': True})
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=name&field=datas&download=true" \
              % (attachment.id)
        return {'name': 'Quyết định nghỉ việc',
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
                }
