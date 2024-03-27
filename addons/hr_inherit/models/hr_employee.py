from odoo import fields, api, models, _
import logging
from odoo.osv import expression

from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)


class HREmployeeInherit(models.Model):
    _inherit = "hr.employee"

    joining_date = fields.Date('Ngày vào làm')
    work_duration = fields.Char('Thâm niên', compute='_get_work_duration')
    resign_date = fields.Date('Ngày nghỉ việc')
    reason_resign = fields.Text('Lý do nghỉ')
    id_issue_date = fields.Date('Ngày cấp CMND/CCCD')
    id_issue_place = fields.Char('Nơi cấp CMND/CCCD')

    @api.depends('joining_date', 'resign_date')
    def _get_work_duration(self):
        for record in self:
            if record.joining_date:
                if record.resign_date:
                    duration = relativedelta(record.resign_date, record.joining_date)
                else:
                    duration = relativedelta(date.today(), record.joining_date)
                y = str(duration.years) + (' năm', ' năm')[duration.years > 1]
                m = str(duration.months) + (' tháng', ' tháng')[duration.months > 1]
                d = str(duration.days) + (' ngày', ' ngày')[duration.days > 1]
                record.work_duration = '%s %s %s' % (('', y)[duration.years > 0],
                                                   ('', m)[duration.months > 0],
                                                   ('', d)[duration.days > 0])





