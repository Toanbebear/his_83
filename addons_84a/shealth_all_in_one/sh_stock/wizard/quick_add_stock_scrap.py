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

class QuickAddStockScrap(models.TransientModel):
    _name = 'quick.add.stock.scrap'
    _description = 'Thêm nhanh Xuất sử dụng phòng/Tiêu hủy'

    type = fields.Selection([('room_use', 'Sử dụng phòng'), ('scrap', 'Tiêu hủy')], string='Loại')
    date_done = fields.Datetime('Ngày xuất', default=lambda self: fields.Datetime.now())
    scrap_location = fields.Many2one('stock.location', string='Địa điểm phế liệu', help='Địa điểm phế liệu')
    room = fields.Many2one('sh.medical.health.center.ot', string='Phòng xuất', help='Phòng xuất',)
    scrap_product_line = fields.Many2many('stock.scrap', string="Dòng chi tiết")
    note = fields.Text("Lý do", compute='compute_note')
    location_id = fields.Many2one('stock.location')

    # xóa sản phẩm đã nhập rồi
    @api.onchange('scrap_product_line')
    def _onchange_scrap_product_line(self):
        if self.scrap_product_line:
            id_products = {}
            inx = 0
            for product in self.scrap_product_line:
                if str(product.product_id.id) in id_products:
                    qty_pro = self.scrap_product_line[
                                  id_products[str(product.product_id.id)]].scrap_qty + product.scrap_qty
                    self.scrap_product_line[id_products[str(product.product_id.id)]].scrap_qty = qty_pro
                    self.scrap_product_line = [(2, product.id, False)]
                    print(product)
                else:
                    # chưa có
                    id_products[str(product.product_id.id)] = inx
                inx += 1


    # thay đổi phòng thì đổ lại bom SDP nếu có
    @api.onchange('room')
    def _onchange_room(self):
        self.location_id = False
        if self.room:
            self.scrap_product_line = False
            self.location_id = self.room.location_supply_stock
            vals = []
            location_id = self.room.location_supply_stock
            vals.append((0, 0, {'sci_date_done': self.date_done,
                                'scrap_qty': 1,
                                'note': self.note,
                                'location_id': location_id.id,
                                'scrap_location_id': self.scrap_location.id,
                                'state': 'draft',
                                'room_use': self.room.id,}))

            self.scrap_product_line = vals

    @api.depends('type', 'date_done')
    def compute_note(self):
        for record in self:
            record.note = ''
            if record.date_done:
                record.note = '%s: %s' % (
                dict(record._fields['type']._description_selection(record.env)).get(record.type),
                record.date_done.strftime("%d/%m/%Y"))

            # thay đổi loại

    @api.onchange('type')
    def _onchange_type(self):
        if self.type:
            self.scrap_product_line = False
            if self.type == 'room_use':
                self = self.with_context(view_for='picking_scrap_room_use', type_stock_scrap='room_use')
                scrap_loc = self.env['stock.location'].search(
                    [('name', 'ilike', 'Sử dụng phòng')], limit=1)
                self.scrap_location = scrap_loc.id
            else:
                self = self.with_context(view_for='picking_scrap', type_stock_scrap='scrap')
                scrap_loc = self.env['stock.location'].search(
                    [('scrap_location', '=', True)], limit=1)
                self.scrap_location = scrap_loc.id
                medicine_room = self.env['sh.medical.health.center.ot'].sudo().search(
                    [('name', 'ilike', 'dược')], limit=1)
                self.room = medicine_room.id
                return {'domain': {'product_id': [('type', 'in', ['product', 'consu'])]}}



    @api.onchange('date_done')
    def _onchange_date_done(self):
        if self.date_done:
            if self.scrap_product_line:
                self.scrap_product_line.note = self.note
                self.scrap_product_line.room_use = self.room
                self.scrap_product_line.sci_date_done = self.date_done



    def quick_add(self):
        if self.room:
            return self.env['stock.picking'].view_stock_picking_by_group('picking_scrap_room_use')

class SHealthStockPicking(models.Model):
    _inherit = 'stock.picking'

    def view_stock_picking_by_group(self, type):
        access_location = []
        domain = []
        context = {}
        name = 'Xuất sử dụng phòng'
        res_model = 'stock.scrap'
        out_location = self.env['stock.location'].sudo().search(
            [('usage', '=', 'internal'),
             ('location_id', 'in', access_location), ('child_ids', '=', False)], limit=1)

        context = {'view_only_name': True,

                  }
        # domain = [('location_id', 'child_of', access_location), ('scrap_location_id.name', 'ilike', 'Sử dụng phòng')]
        view_ids = [(self.env.ref('shealth_all_in_one.sci_stock_scrap_room_use_tree').id, 'tree'),
                    (self.env.ref('shealth_all_in_one.sci_stock_scrap_room_use_form').id, 'form')]
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': context,
            'res_model': res_model,
            'views': view_ids,
            'target': 'current'
        }


class SHealthStockScrap(models.Model):
    _inherit = 'stock.scrap'


    qty_in_loc = fields.Float(string='Số lượng tại tủ', required=True, help="Số lượng khả dụng trong tủ xuất",
                              compute='compute_available_qty_supply_in_location')

    @api.depends('product_id', 'location_id', 'scrap_qty', 'lot_id')
    def compute_available_qty_supply_in_location(self):  # so luong kha dung tai tu
        for record in self:
            if record.product_id:
                quantity_on_hand = self.env['stock.quant']._get_available_quantity(
                    record.product_id,
                    record.location_id,
                    record.lot_id)  # check quantity trong location

                record.qty_in_loc = record.uom_id._compute_quantity(quantity_on_hand,
                                                                    record.product_id.uom_id) if record.product_uom_id != record.product_id.uom_id else quantity_on_hand
            else:
                record.qty_in_loc = 0

            record.is_warning_location = True if (
                    record.scrap_qty > record.qty_in_loc or record.qty_in_loc == 0) else False

