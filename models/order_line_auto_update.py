from odoo import models, fields, api
from odoo.exceptions import Warning
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class SaleOrderLine (models.Model):
    _inherit="sale.order.line"    
    
    purchase_order_line_ids =fields.One2many(
        string='Строки заказа',
        comodel_name='purchase.order.line',
        inverse_name='sale_order_line_id',
    )

class PurchaseOrderLine (models.Model):
    _inherit='purchase.order.line'

    sale_order_line_id = fields.Many2one(
        string='Строка заказа клиента',
        comodel_name='sale.order.line',
    )

    @api.onchange('purchase_status')
    def change_order_line_status(self):
        if (self._origin.sale_order_line_id):
            sale_order_line= self.env['sale.order.line'].search([('id','=',self._origin.sale_order_line_id.id)])
            purchase_order_lines_count = self.env['purchase.order.line'].search_count([('sale_order_line_id', '=', self._origin.sale_order_line_id.id)])
            if (purchase_order_lines_count==1):
                sale_order_line.sudo().write ({'purchase_status':self.purchase_status})
            else:
                purchase_order_lines=self.env['purchase.order.line'].search([('sale_order_line_id','=',self._origin.sale_order_line_id.id)])
                all_lines=True
                for line in purchase_order_lines:
                    if (self._origin.id!=line.id)and(line.purchase_status!=self.purchase_status):
                        all_lines=False
                if (all_lines):
                    sale_order_line.sudo().write ({'purchase_status':self.purchase_status})
            
            sale_order_lines=self.env['sale.order.line'].search([('order_id','=',sale_order_line.order_id.id)])
            all_lines=True
            for lines in sale_order_lines:
                if (lines.purchase_status!='done'):
                    all_lines=False
            if (all_lines):
                sale_order=self.env['sale.order'].search([('id','=',sale_order_line.order_id.id)])
                sale_order.sudo().write ({'sale_order_status_field':True})