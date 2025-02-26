from odoo import fields, api, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime, time
from calendar import monthrange
from openpyxl import load_workbook
from openpyxl.styles import Font, borders, Alignment
import base64
from io import BytesIO
from dateutil.relativedelta import relativedelta
from pytz import timezone, utc

import logging

thin = borders.Side(style='thin')
double = borders.Side(style='double')
all_border_thin = borders.Border(thin, thin, thin, thin)

class ReturnStockScrap(models.TransientModel):
    _name = 'return.stock.scrap'
    _description = 'Hoàn trả thuốc, vật tư tiêu hủy'

    scrap_id = fields.Many2one('stock.scrap', 'Phiếu tiêu hủy', help='Phiếu tiêu hủy')
    sci_date_done = fields.Datetime('Ngày hoàn thành', copy=False, help="Ngày ghi nhận hoàn thành SCI")
    origin = fields.Char('Tài liệu nguồn', help="Tài liệu nguồn")
    note_return = fields.Text('Lý do hoàn chi tiết', help="Ghi nhận lý do hoàn chi tiết")
    location_dest_id = fields.Many2one('stock.location', string='Tủ nhập', help='Địa điểm phế liệu')
    scrap_qty = fields.Float('Số lượng')
    location_id = fields.Many2one('stock.location', 'Tủ xuất', help='Tủ xuất')
    final_lot_id = fields.Many2one('stock.production.lot', 'Số lô/seri')
    product_id = fields.Many2one('product.product', string="Sản phẩm")
    product_uom_id = fields.Many2one('uom.uom', string='đơn vị tính')

    def _prepare_move_values(self):
        return {
            'name': self.scrap_id.name,
            'origin': self.origin,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.scrap_qty,
            'location_id': self.location_id.id,
            'scrapped': True,
            'location_dest_id': self.location_dest_id.id,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                      'product_uom_id': self.product_uom_id.id,
                                      'qty_done': self.scrap_qty,
                                      'location_id': self.location_id.id,
                                      'location_dest_id': self.location_dest_id.id,
                                      'package_id': self.scrap_id.package_id.id,
                                      'lot_id': self.final_lot_id.id if self.final_lot_id else False,
                                      })],
            # 'picking_id': self.picking_id.id
        }

    def post(self):
        if self.final_lot_id:
            # lấy tất cả các lô của sp ở địa điểm tủ hoàn đã chọn
            data_lot_inlocation = self.env['stock.quant'].search([('product_id', '=', self.product_id.id), ('location_id', '=', self.location_dest_id.id), ('lot_id', '=', self.final_lot_id.id)])
            move = self.env['stock.move'].create(self._prepare_move_values())
            move.with_context(is_scrap=True)._action_done()
            #ghi nhận lại ngày hoàn thành stock.move
            move.write({'date': self.scrap_id.sci_date_done or fields.Datetime.now()})
            # ghi nhận lại ngày hoàn thành stock.move.line
            move.move_line_ids.write({'date': self.scrap_id.sci_date_done or fields.Datetime.now()})

            self.scrap_id.write({
                'move_id': move.id,
                'state': 'done',
                'check_return_stock': True,
                'origin': self.origin,
            })
        else:
            data_lot_inlocation = self.env['stock.quant'].search([('product_id', '=', self.product_id.id), ('location_id', '=', self.location_dest_id.id)])
            print('ko có số lô', data_lot_inlocation)
            move = self.env['stock.move'].create(self._prepare_move_values())
            move.with_context(is_scrap=True)._action_done()
            # ghi nhận lại ngày hoàn thành stock.move
            move.write({'date': self.scrap_id.sci_date_done or fields.Datetime.now()})
            # ghi nhận lại ngày hoàn thành stock.move.line
            move.move_line_ids.write({'date': self.scrap_id.sci_date_done or fields.Datetime.now()})

            self.scrap_id.write({
                'move_id': move.id,
                'state': 'done',
                'check_return_stock': True,
                'origin': self.origin,
            })

class SHealthActionReturnStockScrap(models.Model):
    _inherit = 'stock.scrap'


    check_return_stock = fields.Boolean('Hoàn trả', default=False)
    def action_return_validate(self):
        for rec in self:
            return {
                'name': 'Hoàn Tiêu hủy vật tư',
                'view_mode': 'form',
                'res_model': 'return.stock.scrap',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('shealth_all_in_one.return_stock_scrap_form').id,
                'context': {
                    'default_scrap_id': rec.id,
                    'default_product_id': rec.product_id.id,
                    'default_location_id': rec.scrap_location_id.id,
                    'default_product_uom_id': rec.product_uom_id.id,
                    'default_location_dest_id': rec.location_id.id,
                    'default_scrap_qty': rec.scrap_qty,
                    'default_origin': 'Hoản lại phiếu' + ' ' + rec.name,
                    'default_sci_date_done': rec.sci_date_done,
                    'default_final_lot_id': rec.lot_id.id if rec.lot_id else False,
                },
                'target': 'new'
            }
