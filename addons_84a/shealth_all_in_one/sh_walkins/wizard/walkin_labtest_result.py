# -*- coding: utf-8 -*-

import json
from lxml import etree
from odoo import api, fields, models
import datetime
from datetime import timedelta
from odoo.tools import float_is_zero, float_compare, pycompat


class WalkinLabtestsResult(models.TransientModel):
    _name = 'walkin.labtest.result'
    _description = 'Walkin labtest result'

    patient = fields.Many2one('sh.medical.patient', string='Bệnh nhân', help="Tên bệnh nhân", readonly=True)
    service = fields.Many2many('sh.medical.health.center.service', 'sh_walkin_labtest_result_service_rel', 'walkin_labtest_result_id', 'service_id',
                               readonly=True, string='Dịch vụ')
    requestor = fields.Many2one('sh.medical.physician', 'Bác sĩ chỉ định')
    pathologist = fields.Many2one('sh.medical.physician', 'Kỹ thuật viên', default=lambda self: self.env.ref('__import__.data_physician_2', False) )
    date_exam = fields.Datetime('Ngày khám', readonly=True)
    date_requested = fields.Datetime('Ngày yêu cầu')
    date_analysis = fields.Datetime('Ngày phân tích')
    date_done = fields.Datetime('Ngày trả kết quả')

    # @api.model
    # def fields_view_get_backup(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     self.env['ir.actions.actions'].clear_caches()
    #     res = super(WalkinLabtestsResult, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if view_id == self.env.ref('shealth_all_in_one.walkin_labtest_result_view_form').id:
    #         doc = etree.XML(res['arch'])
    #         all_fields = {}
    #         walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.env.context.get('active_id'))
    #         lab_tests = walkin.lab_test_ids.filtered(lambda l: l.state != 'Completed')
    #         lab_groups = lab_tests.mapped('group_type')
    #         for group in lab_groups:
    #             etree.SubElement(doc, 'separator', {'string': group.name})
    #             xml_lab_group = etree.SubElement(doc, 'group', {'col': '3'})
    #             etree.SubElement(xml_lab_group, 'span').text = '<b>Xét nghiệm</b>'
    #             etree.SubElement(xml_lab_group, 'span').text = '<b>Kết quả</b>'
    #             etree.SubElement(xml_lab_group, 'span').text = '<b>Khoảng bình Thường</b>'
    #             for lab_test in lab_tests.filtered(lambda t: t.group_type == group):
    #                 test_group = etree.SubElement(doc, 'group', {'col': '3'})
    #                 span1 = etree.SubElement(test_group, 'span')
    #                 b = etree.SubElement(span1, 'i')
    #                 b.text = lab_test.test_type.name
    #                 if not lab_test.lab_test_criteria:
    #                     field_name = 'result_%s' % lab_test.id
    #                     etree.SubElement(test_group, 'field', {'name': field_name, 'nolabel': '1', 'required': '1'})
    #                     for node in doc.xpath("//field[@name='%s']" % field_name):
    #                         node.set("required", "1")
    #                         node.set("modifiers", json.dumps({'required': True}))
    #                     all_fields[field_name] = {'type': 'text',
    #                                               'string': 'Result',
    #                                               'exportable': False,
    #                                               'selectable': False}
    #                     etree.SubElement(test_group, 'span').text = '_'
    #                 else:
    #                     etree.SubElement(test_group, 'span').text = '_'
    #                     etree.SubElement(test_group, 'span').text = '_'
    #                     for criteria in lab_test.lab_test_criteria:
    #                         c_group = etree.SubElement(doc, 'group', {'col': '3'})
    #                         c_span1 = etree.SubElement(c_group, 'span')
    #                         c_span1.text = criteria.name
    #                         c_field_name = 'result_%s_%s' % (lab_test.id, criteria.id)
    #                         etree.SubElement(c_group, 'field', {'name': c_field_name, 'nolabel': '1', 'required': '1'})
    #                         for node in doc.xpath("//field[@name='%s']" % c_field_name):
    #                             node.set("required", "1")
    #                             node.set("modifiers", json.dumps({'required': True}))
    #                         all_fields[c_field_name] = {'type': 'char',
    #                                                     'string': 'Result',
    #                                                     'exportable': False,
    #                                                     'selectable': False}
    #                         c_span3 = etree.SubElement(c_group, 'span')
    #                         c_span3.text = ' '.join([criteria.normal_range or '', criteria.units.name or ''])
    #         res['arch'] = etree.tostring(doc, encoding='unicode')
    #         res['fields'].update(all_fields)
    #         # print(res)
    #     return res

    @api.onchange('date_analysis')
    def onchange_date_analysis(self):
        if not isinstance(self.date_analysis, pycompat.string_types) and self.date_analysis:
            self.date_requested = datetime.datetime.strptime(self.date_analysis.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S") - timedelta(minutes=10) or fields.Datetime.now()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        self.env['ir.actions.actions'].clear_caches()
        res = super(WalkinLabtestsResult, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_id == self.env.ref('shealth_all_in_one.walkin_labtest_result_view_form').id:
            doc = etree.XML(res['arch'])
            all_fields = {}
            walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.env.context.get('active_id'))
            lab_tests = walkin.lab_test_ids.filtered(lambda l: l.state != 'Completed')
            lab_groups = lab_tests.mapped('group_type')
            for group in lab_groups:
                xml_lab_group = etree.SubElement(doc, 'group', {'col': '3', 'string': group.name, 'class': 'sh_result_labtest'})
                etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '<b>Loại Xét nghiệm</b>'
                etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '<b>Kết quả</b>'
                etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '<b>Khoảng bình Thường</b>'
                index = 1
                for lab_test in lab_tests.filtered(lambda t: t.group_type == group):
                    span1 = etree.SubElement(xml_lab_group, 'span')
                    b = etree.SubElement(span1, 'b', {'class': 'text-primary'})
                    b.text = '. '.join([str(index), lab_test.test_type.name])

                    index += 1

                    if not lab_test.lab_test_criteria:
                        field_name = 'result_%s' % lab_test.id
                        etree.SubElement(xml_lab_group, 'field', {'name': field_name, 'nolabel': '1', 'required': '1'})
                        for node in doc.xpath("//field[@name='%s']" % field_name):
                            node.set("required", "1")
                            node.set("modifiers", json.dumps({'required': True}))
                        all_fields[field_name] = {'type': 'char',
                                                  'string': 'Result',
                                                  'exportable': False,
                                                  'selectable': False}
                        etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '_'
                    else:
                        etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '_'
                        etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'}).text = '_'
                        for criteria in lab_test.lab_test_criteria:
                            c_span1 = etree.SubElement(xml_lab_group, 'span', {'class': 'ml-3'})
                            c_span1.text = criteria.name
                            c_field_name = 'result_%s_%s' % (lab_test.id, criteria.id)
                            etree.SubElement(xml_lab_group, 'field', {'name': c_field_name, 'nolabel': '1', 'required': '1'})
                            for node in doc.xpath("//field[@name='%s']" % c_field_name):
                                node.set("required", "1")
                                node.set("modifiers", json.dumps({'required': True}))
                            all_fields[c_field_name] = {'type': 'char',
                                                        'string': 'Result',
                                                        'exportable': False,
                                                        'selectable': False}
                            c_span3 = etree.SubElement(xml_lab_group, 'span', {'class': 'ml-5'})
                            c_span3.text = ' '.join([criteria.normal_range or '', criteria.units.name or ''])
            footer = etree.SubElement(doc, 'footer')
            etree.SubElement(footer, 'button', {'string': 'Trả kết quả', 'name': 'action_apply', 'type': 'object', 'class': 'btn-primary'})
            etree.SubElement(footer, 'button', {'string': 'Hủy', 'special': 'cancel', 'class': 'btn-secondary'})
            res['arch'] = etree.tostring(doc, encoding='unicode')
            res['fields'].update(all_fields)
            # print(res)
        return res

    @api.model
    def create(self, vals):
        # print(vals)
        walkin = self.env['sh.medical.appointment.register.walkin'].browse(self.env.context.get('active_id'))
        for lab_test in walkin.lab_test_ids.filtered(lambda l: l.state != 'Completed'):
            lab_test.set_to_test_inprogress()
            test_vals = {'pathologist': vals.get('pathologist'),
                         'requestor': vals.get('requestor'),
                         'date_analysis': vals.get('date_analysis'),
                         'date_done': vals.get('date_done'),
                         'date_requested': vals.get('date_requested')}
            if not lab_test.lab_test_criteria:
                test_vals['results'] = vals.get('result_%s' % lab_test.id)
            else:
                for criteria in lab_test.lab_test_criteria:
                    criteria.result = vals.get('result_%s_%s' % (lab_test.id, criteria.id))
            lab_test.write(test_vals)
            lab_test.set_to_test_complete()
        return super(WalkinLabtestsResult, self).create({})

    def action_apply(self):
        return {'type': 'ir.actions.act_window_close'}
