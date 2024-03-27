from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, AccessError
import collections


class WizardChooseStockPicking(models.TransientModel):
    _name = 'choose.stock.picking'

    purchase_id = fields.Many2one('purchase.order', string='Đơn mua hàng')
    picking_ids = fields.Many2many('stock.picking', string='Phiếu điều chuyển')

    def add_stock_picking(self):
        # Check Purchase Order với Stock Picking
        if any(picking.purchase_id for picking in self.picking_ids):
            raise UserError(_('Có Stock Picking tồn tại Purchase Order, hãy kiểm tra lại.'))

        # Check Partner trong Purchase Order với Stock Picking
        if any(picking.partner_id.id != self.purchase_id.partner_id.id for picking in self.picking_ids):
            raise UserError(_('Đối tác trong Stock Picking khác với Purchase Order, hãy kiểm tra lại.'))

        # Check mặt hàng, số lượng trong toàn bộ Stock Picking với Purchar Order
        # TODO check về mặt hàng, số lượng, đơn vị tính giữa PO và Pickings (stock.move = picking.move_lines)
        purchase_order_lines = self.purchase_id.order_line.filtered(lambda x: x.state == 'purchase')
        grouped_po = collections.defaultdict(float)
        grouped_product = collections.defaultdict(float)
        for line in purchase_order_lines:
            grouped_po[line.product_id, line.product_id.uom_id] += line.product_qty
            grouped_product[line.product_id] = line.product_uom

        for picking in self.picking_ids:
            move_lines = picking.move_lines.filtered(lambda x: x.state == 'done')
            grouped_picking = collections.defaultdict(float)
            for move_line in move_lines:
                grouped_picking[move_line.product_id, move_line.product_uom] += \
                    move_line.product_uom._compute_quantity(move_line.product_uom_qty,
                                                             grouped_product.get(move_line.product_id), rounding_method='HALF-UP')

        if all(grouped_picking.get(key) == grouped_po.get(key) for key in grouped_po.keys()):
            for picking in self.picking_ids:
                if any(
                        (self.purchase_id.picking_type_id.id == picking.picking_type_id.id,
                         self.purchase_id.partner_id.id == picking.purchase_id,
                         self.purchase_id._get_destination_location() == picking.location_dest_id.id,
                         self.purchase_id.partner_id.property_stock_supplier.id == picking.location_id.id,
                         self.purchase_id.company_id.id == picking.company_id)
                ):

                    # Gán Picking vào PO và sửa ngày đặt hàng bằng trong Picking
                    self.purchase_id.write({
                        'date_order': picking.sci_date_done,
                        'picking_ids': [(4, picking.id)]
                    })

                    # Gán Purchase Orrder Line cho Stock Move Line tương ứng
                    for pol in self.purchase_id.order_line:
                        move_line = picking.move_lines.filtered(lambda x: x.product_id.id == pol.product_id.id and x.state != 'cancel')
                        move_line.write({'purchase_line_id': pol.id})

            picking_refund = self.purchase_id.picking_ids
            check_refund = False
            for picking in picking_refund.filtered(lambda x: "OUT" in x.name):
                for line in picking.move_lines:
                    line.write({'to_refund': True})
                    check_refund = True
            if check_refund:
                for line in self.purchase_id.order_line:
                    line._update_received_qty()
        else:
            raise UserError(_('Số lượng hoặc mặt hàng trong PO không khớp với Picking.'))

        # Update số lượng thực nhận
        for line in self.purchase_id.order_line:
            line._update_received_qty()
