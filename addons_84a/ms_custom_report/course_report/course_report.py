# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import date, datetime, time
from calendar import monthrange
from openpyxl import load_workbook
from openpyxl.styles import Font, borders, Alignment
import base64
from io import BytesIO
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)


class MonthlyCourseReport(models.TransientModel):
    _name = 'op.course.report'
    _description = 'Monthly Course Report'

    report_type = fields.Selection([('course', 'Course report'), ('batch', 'Batch report')], 'Report type', default='course')
    course = fields.Many2one('op.course', string='Course')
    departments = fields.Many2many('hr.department', string='Departments')
    student_status = fields.Selection([('not', 'Not learned'), ('finish', 'Finished')], string='Status')

    courses = fields.Many2many('op.course', string='Courses')
    faculties = fields.Many2many('op.faculty', string='Faculties')
    # product_domain = fields.Many2many('product.product', compute='_get_product_domain')
    start_date = fields.Date('Start date', default=date.today().replace(day=1))
    end_date = fields.Date('End date')
    institutes = fields.Many2many('op.institute', string='Institutes')
    # @api.one
    # @api.depends('location')
    # def _get_product_domain(self):
    #     self.product_domain = self.env['stock.quant'].search([('location_id', 'child_of', self.location.id)]).mapped('product_id')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            if self.start_date.month == fields.date.today().month:
                self.end_date = fields.date.today()
            else:
                self.end_date = date(self.start_date.year, self.start_date.month,
                                     monthrange(self.start_date.year, self.start_date.month)[1])

    @api.multi
    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        for record in self:
            start_date = fields.Date.from_string(record.start_date)
            end_date = fields.Date.from_string(record.end_date)
            if start_date > end_date:
                raise ValidationError(
                    _("End Date cannot be set before Start Date."))

    def report_course(self):
        template = self.env.ref('ms_custom_report.internal_course_report')
        domain = [('course_id', '=', self.course.id)]
        if self.departments:
            domain += [('department_id', 'in', self.departments.ids)]
        if self.institutes:
            batch_ids = self.env['op.batch'].search([('institute', 'in', self.institutes.ids), ('start_date', '>', self.start_date), ('start_date', '<', self.end_date)]).ids
            domain += [('batch_id', 'in', batch_ids)]
        if self.student_status:
            if self.student_status == 'not':
                domain += [('status', 'in', ['not', 'study'])]
            elif self.student_status == 'finish':
                domain += [('batch_start_date', '>', self.start_date), ('batch_start_date', '<', self.end_date), ('status', '=', 'finish')]
            records = self.env['op.student.course'].search(domain)
        else:
            domain1 = domain + [('batch_start_date', '>', self.start_date), ('batch_start_date', '<', self.end_date)]
            domain2 = domain + [('batch_id', '=', False)]
            records = self.env['op.student.course'].search(domain2) + self.env['op.student.course'].search(domain1)
        return {'name': (_('Internal course report')),
                'type': 'ir.actions.act_window',
                'res_model': 'temp.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'inline',
                'view_id': self.env.ref('ms_templates.report_wizard').id,
                'context': {'default_template_id': template.id, 'active_ids': records.ids, 'active_model': 'op.student.course'}}

    def report_batch(self):
        template = self.env.ref('ms_custom_report.internal_batch_report')
        domain = [('start_date', '>', self.start_date), ('start_date', '<', self.end_date)]
        if self.courses:
            domain += [('course_id', 'in', self.courses.ids)]
        if self.faculties:
            domain += [('faculty_id', 'in', self.faculties.ids)]
        if self.institutes:
            domain += [('institute', 'in', self.institutes.ids)]

        records = self.env['op.batch'].search(domain)
        return {'name': (_('Internal batch report')),
                'type': 'ir.actions.act_window',
                'res_model': 'temp.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'inline',
                'view_id': self.env.ref('ms_templates.report_wizard').id,
                'context': {'default_template_id': template.id, 'active_ids': records.ids,
                            'active_model': 'op.batch'}}

    # def student_course_pivot(self):
    #     return {'name': (_('Internal course pivot')),
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'op.student.course',
    #             'view_type': 'form',
    #             'view_mode': 'pivot,graph,tree,form',
    #             'domain': [('course_id.internal', '=', True),
    #                        ('batch_start_date', '>', self.start_date), ('batch_start_date', '<', self.end_date)]}

        # url = "/web/content/?model=ir.attachment&id=%s&filename_field=datas_fname&field=datas&download=true&filename=Stock cards.xlsx" \
        #       % (attachment.id)
        # cron_clean_attachment = self.env.ref('ms_templates.clean_attachments')
        # cron_clean_attachment.sudo().nextcall = fields.Datetime.now() + relativedelta(seconds=10)
        # return {'name': 'Stock cards',
        #         'type': 'ir.actions.act_url',
        #         'url': url,
        #         'target': 'self',
        #         }
