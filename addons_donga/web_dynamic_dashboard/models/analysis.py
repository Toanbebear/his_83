
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError

class AccountMoveAnalysis(models.Model):
    _name = 'analysis.account.move.line'
    _description = " Analysis : Account Move Line"
    _auto = False

    balance = fields.Float('Balance')
    abs_balance = fields.Float('Absolute Balance')
    reversed_balance = fields.Float('Reversed Balance')
    accont_code = fields.Char('Code')
    account_name = fields.Char('Account')
    account_type_name = fields.Char('Account Type')
    partner_id = fields.Many2one('res.partner', 'Partner')

    move_date = fields.Date('Date')
    company_id = fields.Many2one('res.company', 'Company')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT 
                aml.id AS id,
                balance,
                abs(balance) AS abs_balance,
                -balance AS reversed_balance,
                aa.code AS accont_code,
                aa.name AS account_name,
                aat.name AS account_type_name,
                aml.date AS move_date,
                aml.partner_id AS partner_id,
                aml.company_id as company_id
            FROM account_move_line aml
            LEFT JOIN account_account aa on (aml.account_id = aa.id)
            LEFT JOIN account_account_type aat on (aa.user_type_id = aat.id)
        )""" % (self._table,))

class SaleAnalysis(models.Model):
    _name = "analysis.sale"
    _description = " Analysis : Sale"
    _auto = False

    # Measure
    sale_total = fields.Float('Total Net Sales')
    sale_discount = fields.Float('Discount Amount')
    product_uom_qty = fields.Float('Product Qty')
    sale_margin = fields.Float('Total Margin')
    sale_gross = fields.Float('Gross Sales')
    sale_tax = fields.Float('Tax Amount')
    delivered_qty = fields.Float('Delivered Qty')
    invoiced_qty = fields.Float('Invoiced Qty')
    sale_cost = fields.Float('Total Cost')

    # Dimension
    date_order = fields.Datetime('Date Order')

    product_name = fields.Char('Product')
    product_category_name = fields.Char('Product Category')
    partner_name = fields.Char('Customer')
    partner_id = fields.Many2one('res.partner', 'Customer')
    saleperson_name = fields.Char('Saleperson')
    saleperson_id = fields.Many2one('res.users', 'Saleperson')
    sale_state = fields.Char('Sale Order Status')
    state_name = fields.Char('Customer Address (State)')
    invoice_status = fields.Char('Invoice Status')
    saleteam_name = fields.Char('Salesteam')
    
    company_id = fields.Many2one('res.company', 'Company')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT
                sale_order_line.id AS id,
                sale_order_line.price_unit * sale_order_line.product_uom_qty AS sale_gross,
                sale_order_line.price_unit * sale_order_line.product_uom_qty * sale_order_line.discount / 100 AS sale_discount,
                sale_order_line.price_tax AS sale_tax,
                sale_order_line.price_subtotal AS sale_without_tax,
                sale_order_line.price_total AS sale_total,
                sale_order_line.discount AS sale_discount_percentage,
                sale_order_line.product_uom_qty AS product_uom_qty,
                sale_order_line.price_unit * sale_order_line.product_uom_qty AS sale_cost,
                sale_order_line.price_total - (sale_order_line.price_unit * sale_order_line.product_uom_qty) AS sale_margin,
                sale_order_line.qty_delivered AS delivered_qty,
                sale_order_line.qty_invoiced AS invoiced_qty,
                sale_order_line.invoice_status AS invoice_status,
                sale_order_line.state AS sale_state,
                saleperson.name AS saleperson_name,
                res_users.id AS saleperson_id,
                crm_team.name AS saleteam_name,
                product_template.name AS product_name, 
                res_partner.name AS partner_name, 
                res_partner.id AS partner_id,
                product_category.name AS product_category_name,
                sale_order.date_order AS date_order,
                res_country_state.name AS state_name,
                sale_order.company_id as company_id
            FROM sale_order_line
            LEFT JOIN sale_order ON (sale_order.id = sale_order_line.order_id)
            LEFT JOIN res_partner ON (sale_order.partner_id = res_partner.id)
            LEFT JOIN product_product ON (product_product.id = sale_order_line.product_id)
            LEFT JOIN product_template ON (product_template.id = product_product.product_tmpl_id)
            LEFT JOIN product_category ON (product_category.id = product_template.categ_id)
            LEFT JOIN res_users ON (res_users.id = sale_order_line.salesman_id)
            LEFT JOIN res_partner saleperson ON (res_users.partner_id = saleperson.id)
            LEFT JOIN crm_team ON (res_users.sale_team_id = crm_team.id)
            LEFT JOIN res_country_state ON (res_partner.state_id = res_country_state.id)
        )""" % (self._table,))


class StockQuantAnalysis(models.Model):
    _name = "analysis.stock.quant"
    _description = " Analysis : Stock Quant"
    _auto = False

    product_name = fields.Char('Product Name')
    location_name = fields.Char('Location Name')
    categ_name = fields.Char('Category Name')
    stock_qty = fields.Float('Qty')
    stock_value = fields.Float('Valuation')
    incoming_date = fields.Datetime('Incoming Date')
    stock_duration = fields.Float('Stock Duration (Days)')  
    storage_duration_category = fields.Selection([
        ('1week', '1 Week'), 
        ('1month', '1 Month'),  
        ('3months', '3 Months'), 
        ('6months', '6 Months'), 
        ('1year', '1 Year'), 
        ('over1year', 'Over a Year')], string='Stock Status')

    company_id = fields.Many2one('res.company', 'Company')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT 
                sq.id as id,
                pt.name as product_name, 
                sl.complete_name as location_name, 
                pcg.name AS categ_name,
                sq.quantity AS stock_qty,
                ir_property.value_float AS stock_cost,
                sq.quantity * ir_property.value_float AS stock_value,
                sq.in_date AS incoming_date,
                DATE_PART('day', (CURRENT_DATE::timestamp - sq.in_date)) AS stock_duration,
                CASE
                    WHEN
                        CURRENT_DATE::timestamp - sq.in_date <= interval '7 day'
                        THEN '1week'
                    WHEN
                        CURRENT_DATE::timestamp - sq.in_date <= interval '1 month'
                        THEN '1month'
                    WHEN
                        CURRENT_DATE::timestamp - sq.in_date <= interval '3 month'
                        THEN '3months'
                    WHEN
                        CURRENT_DATE::timestamp - sq.in_date <= interval '6 month'
                        THEN '6months'
                    WHEN
                        CURRENT_DATE::timestamp - sq.in_date <= interval '1 year'
                        THEN '1year'
                    ELSE 'other' 
                END AS storage_duration_category,
                sq.company_id AS company_id
            FROM stock_quant sq 
            LEFT JOIN stock_location sl ON (sl.id = sq.location_id)
            LEFT JOIN stock_warehouse_orderpoint swo ON (swo.product_id = sq.product_id)
            LEFT JOIN product_product pp ON (pp.id = sq.product_id)
            LEFT JOIN product_template pt ON (pt.id = pp.product_tmpl_id)
            LEFT JOIN product_category pcg ON (pcg.id = pt.categ_id)
            LEFT JOIN ir_property ON (ir_property.res_id = concat('product.product,', sq.product_id::text))
        )""" % (self._table,))

class StockAnalysis(models.Model):
    _name = "analysis.stock.move"
    _description = " Analysis : Stock Move"
    _auto = False

    product_name = fields.Char('Product')
    categ_name = fields.Char('Product Category')
    location_name = fields.Char('Location')
    location_other_name = fields.Char('Location From/To')
    location_other_usage = fields.Char('Location From/To Category')
    move_type = fields.Char('Move Type (In/Out)')

    product_qty = fields.Float('Qty')
    product_signed_qty = fields.Float('Signed Qty')

    # value = fields.Float('Value')
    # signed_value = fields.Float('Signed Value')
    # price_unit = fields.Float('Unit Price')
    value_current_cost = fields.Float('Value (Current Cost)')
    signed_value_current_cost = fields.Float('Signed Value (Current Cost)')
    current_cost = fields.Float('Current Cost')
    date = fields.Datetime('Date')
    date_expected = fields.Datetime('Expected Date')

    company_id = fields.Many2one('res.company', 'Company')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT 
                stock_move_location.id,
                product_name,
                stock_move_location.product_id,
                location_name,
                location_other_name,
                location_usage,
                location_other_usage,
                product_qty,
                product_signed_qty,
                move_type,
                COALESCE(ir_property.value_float, 0) AS current_cost,
                COALESCE(ir_property.value_float, 0) * product_qty AS value_current_cost,
                COALESCE(ir_property.value_float, 0) * product_signed_qty AS signed_value_current_cost,
                COALESCE(price_unit, 0) AS price_unit,
                COALESCE(price_unit, 0) * product_qty AS value,
                COALESCE(price_unit, 0) * product_signed_qty AS signed_value,
                date,
                date_expected,
                categ_name,
                stock_move_location.company_id as company_id
            FROM
                (SELECT 
                    -stock_move.id AS id,
                    product_template.name AS product_name,
                    stock_move.product_id AS product_id,
                    product_qty AS product_qty,
                    -product_qty AS product_signed_qty,
                    location_from.complete_name AS location_name,
                    location_dest.complete_name AS location_other_name,
                    location_from.usage AS location_usage,
                    location_dest.usage AS location_other_usage,
                    'out' AS move_type,
                price_unit,
                date,
                date_expected,
                product_category.name as categ_name,
                stock_move.company_id as company_id
            FROM stock_move
            LEFT JOIN product_product ON (product_product.id = stock_move.product_id)
            LEFT JOIN product_template ON (product_template.id = product_product.product_tmpl_id)
            LEFT JOIN stock_location location_from ON (location_from.id = stock_move.location_id)
            LEFT JOIN stock_location location_dest ON (location_dest.id = stock_move.location_dest_id)
            LEFT JOIN product_category ON (product_category.id = product_template.categ_id)
            WHERE stock_move.state='done'
            UNION ALL SELECT 
                stock_move.id AS id,
                product_template.name AS product_name,
                stock_move.product_id AS product_id,
                product_qty AS product_qty,
                product_qty AS product_signed_qty,
                location_dest.complete_name AS location_name,
                location_from.complete_name AS location_other_name,
                location_dest.usage AS location_usage,
                location_from.usage AS location_other_usage,
                'in' AS move_type,
                price_unit,
                date,
                date_expected,
                product_category.name as categ_name,
                stock_move.company_id as company_id
            FROM stock_move
            LEFT JOIN product_product ON (product_product.id = stock_move.product_id)
            LEFT JOIN product_template ON (product_template.id = product_product.product_tmpl_id)
            LEFT JOIN stock_location location_from ON (location_from.id = stock_move.location_id)
            LEFT JOIN stock_location location_dest ON (location_dest.id = stock_move.location_dest_id)
            LEFT JOIN product_category ON (product_category.id = product_template.categ_id)
            WHERE stock_move.state='done') AS stock_move_location
            LEFT JOIN ir_property 
                ON (ir_property.res_id = concat('product.product,', stock_move_location.product_id::text) 
            AND ir_property.name = 'standard_price')
        )""" % (self._table,))
