# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, time
from calendar import monthrange
from openpyxl import load_workbook
from openpyxl.styles import Font, borders, Alignment
import base64
from io import BytesIO
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)

thin = borders.Side(style='thin')
double = borders.Side(style='double')
all_border_thin = borders.Border(thin, thin, thin, thin)


class SurgeryReport(models.TransientModel):
    _name = 'surgery.report'
    _description = 'Báo cáo hoạt động phẫu thuật thủ thuật'

    start_date = fields.Date('Start date', default=date.today().replace(day=1))
    end_date = fields.Date('End date')

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

    def report_surgery(self):
        template = self.env.ref('shealth_all_in_one.bao_cao_loai_phau_thuat')
        start_date = self.start_date
        end_date = self.end_date
        if start_date.month != end_date.month:
            raise UserError(_('Nhập ngày bắt đầu và kết thúc trong cùng một tháng'))
        if start_date.day != 1:
            raise UserError(_('Nhập ngày bắt đầu là mùng 1'))
        total_surgery_special_count = total_surgery_3_count = total_surgery_2_count = total_surgery_1_count = 0

        if start_date.month > 1:
            total_surgery_special_count = self.env['sh.medical.surgery'].search_count([('state', '!=', 'Draft'),
                                                                                  ('surgery_date', '>=', start_date),
                                                                                  ('surgery_date', '<=', end_date),
                                                                                  ('surgery_type', '=', 'DB')])

            total_surgery_3_count = self.env['sh.medical.surgery'].search_count([('state', '!=', 'Draft'),
                                                                                       ('surgery_date', '>=',
                                                                                        start_date),
                                                                                       ('surgery_date', '<=', end_date),
                                                                                       ('surgery_type', '=', '3')])

            total_surgery_2_count = self.env['sh.medical.surgery'].search_count([('state', '!=', 'Draft'),
                                                                                       ('surgery_date', '>=',
                                                                                        start_date),
                                                                                       ('surgery_date', '<=', end_date),
                                                                                       ('surgery_type', '=', '2')])

            total_surgery_1_count = self.env['sh.medical.surgery'].search_count([('state', '!=', 'Draft'),
                                                                                 ('surgery_date', '>=',
                                                                                  start_date),
                                                                                 ('surgery_date', '<=', end_date),
                                                                                 ('surgery_type', '=', '1')])



        external_keys = {'f3': start_date.strftime('Tháng %m Năm %Y'),
                         'b2': self.env.user.company_id.name,
                         'd10': total_surgery_special_count, 'e10': total_surgery_special_count,
                         'd11': total_surgery_1_count, 'e11': total_surgery_1_count,
                         'd12': total_surgery_2_count, 'e12': total_surgery_2_count,
                         'd13': total_surgery_3_count, 'e13': total_surgery_3_count,
                         }

        return {'name': (_('Báo cáo phẫu thuật thủ thuật')),
                'type': 'ir.actions.act_window',
                'res_model': 'temp.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'inline',
                'view_id': self.env.ref('ms_templates.report_wizard').id,
                'context': {'default_template_id': template.id, 'external_keys': external_keys,
                            'active_model': 'sh.medical.surgery'}}
