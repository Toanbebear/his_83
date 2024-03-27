# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
import logging

from dateutil.relativedelta import relativedelta
from urllib.parse import quote

_logger = logging.getLogger(__name__)


class TemplateWizard(models.TransientModel):
    _name = 'temp.wizard'
    _description = 'temp.wizard'

    ms_url = fields.Char('URL')
    framed_page_rendered = fields.Html('Embedded Webpage', default=lambda self: self.get_report(), sanitize=False, strip_style=False)

    @api.multi
    def get_report(self):
        """This function will take attachment id from custom report or template id and active ids to create attachment,
        then render it to microsoft online iframe"""

        if self._context.get('attachment_id'):
            attachment = self.env['ir.attachment'].browse(self._context.get('attachment_id'))
        else:
            external_keys = self._context.get('external_keys') or {}
            template_id = self.env['temp.creation'].browse(self._context.get('default_template_id'))
            model = self._context.get('active_model')
            records = self.env[model].browse(self.env.context.get('active_ids'))
            attachment = self.env['ir.attachment'].sudo().create({'name': 'MS report',
                                                                  'datas_fname': template_id.template_name,
                                                                  'datas': template_id.export_records_data(records, **external_keys),
                                                                  'res_model': 'temp.creation',
                                                                  'res_id': template_id.id,
                                                                  'public': True})
        office_url = 'https://view.officeapps.live.com/op/view.aspx?src='
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = "/web/content/?model=ir.attachment&id=%s&filename_field=datas_fname&field=datas&download=true&filename=%s" \
              % (attachment.id, attachment.datas_fname)
        ms_url = office_url + quote((base_url + url), safe='~()*!.\'')
        template = self.env.ref('ms_templates.framed_page')
        cron_clean_attachment = self.env.ref('ms_templates.clean_attachments')
        cron_clean_attachment.sudo().nextcall = fields.datetime.now() + relativedelta(seconds=25)

        # chạy excel trên server
        return template.render({'url': ms_url})

        # chạy excel local
        # return base_url + url

# http://sandbox.scisoftware.xyz/web/content/?model=ir.attachment&id=4739&filename_field=datas_fname&field=datas&download=true&filename=test.xlsx
        # elif extension == 'docx':
        #     doc = Document(io.BytesIO(decode))
        #     if len(records) == 1:
        #         for p in doc.paragraphs:
        #             for line in template_id.chosen_fields:
        #                 if line.temp_mark in p.text:
        #                     for run in p.runs:
        #                         if line.main_field.ttype not in ['one2many', 'many2many'] and run.text == line.temp_mark:
        #                             run.text = str(self.get_field_value(records, line.main_field, line.sub_field))
        #         for t in doc.tables:
        #             for r in range(len(t.rows)):
        #                 for c in range(len(t.columns)):
        #                     for line in template_id.chosen_fields:
        #                         if t.cell(r, c).text == line.temp_mark and line.main_field.ttype in ['one2many', 'many2many']:
        #                             if template_id.export_horizontally:
        #                                 sub_records = self.get_field_value(records, line.main_field)
        #                                 for i in range(len(sub_records)):
        #                                     t.cell(r, c + i).paragraphs[0].runs[0].text = \
        #                                         str(self.get_field_value(sub_records[i], line.sub_field))
        #                             else:
        #                                 sub_records = self.get_field_value(records, line.main_field)
        #                                 for i in range(len(sub_records)):
        #                                     t.cell(r + i, c).paragraphs[0].runs[0].text = \
        #                                         str(self.get_field_value(sub_records[i], line.sub_field))
        #                         elif line.temp_mark in t.cell(r, c).text and line.main_field.ttype not in ['one2many', 'many2many']:
        #                             for run in t.cell(r, c).paragraphs[0].runs:
        #                                 if run.text == line.temp_mark:
        #                                     run.text = str(self.get_field_value(records, line.main_field, line.sub_field))
        #     else:
        #         for t in doc.tables:
        #             for r in range(len(t.rows)):
        #                 for c in range(len(t.columns)):
        #                     for line in template_id.chosen_fields:
        #                         for i in range(len(records)):
        #                             if t.cell(r, c).text == line.temp_mark and template_id.export_horizontally:
        #                                 t.cell(r, c + i).paragraphs[0].runs[0].text = \
        #                                     str(self.get_field_value(records[i], line.main_field, line.sub_field))
        #                             elif t.cell(r, c).text == line.temp_mark and not template_id.export_horizontally:
        #                                 t.cell(r + i, c).paragraphs[0].runs[0].text = \
        #                                     str(self.get_field_value(records[i], line.main_field, line.sub_field))
        #
        #     fp = BytesIO()
        #     doc.save(fp)
        #     fp.seek(0)
        #     report = base64.encodebytes((fp.read()))
        #     fp.close()
        #
        # else:
        #     raise ValidationError(_("Wrong template extension, please contact your admin"))

        # def _compute_iframe(self):
        #     url = self.ms_url
        #     template = self.env.ref('ms_templates.framed_page')
        #     self.framed_page_rendered = template.render({'url': url})