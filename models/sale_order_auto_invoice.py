from odoo import models, fields, api
from odoo.exceptions import Warning
from odoo.exceptions import UserError

class SaleOrderAutoInvoice (models.Model):
    _inherit="sale.order"

    


    def action_confirm(self):
        super(SaleOrderAutoInvoice,self).action_confirm()
        self.env.user.notify_info('My information message')
        payment = self.env['sale.advance.payment.inv'].create({'advance_payment_method': 'all'})
        payment.with_context(active_ids=self.id).create_invoices()        
        invoices = self.mapped('invoice_ids')
        for invoice in invoices:
            invoice._compute_utm_from_origin()
        # for invoice in invoices:
            # invoice.description=self.x_studio_field_7NjeR
            # invoice.action_invoice_open()
    
    def create_invoice_button(self):
        payment = self.env['sale.advance.payment.inv'].create({'advance_payment_method': 'all'})
        payment.with_context(active_ids=self.id).create_invoices()        
        invoices = self.mapped('invoice_ids')
        for invoice in invoices:
            invoice._compute_utm_from_origin()
        # for invoice in invoices:
        #     if (invoice.state == 'draft'):
                # invoice.description=self.x_studio_field_7NjeR
                # invoice.action_invoice_open()



class SaleOrderLine (models.Model):
    _inherit="sale.order.line" 

    #do not change price_unit after changing product_uom
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_id:
            self.price_unit = 0.0
            return
    
    #Add product_info field to account.invoice.line
    @api.model
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty=self.product_uom_qty)
        res.update({
            'product_info': self.product_info,
            })
        return res


class PurchaseOrderLine (models.Model):
    _inherit="purchase.order.line"

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     result = super(PurchaseOrderLine,self).onchange_product_id()
    #     self.price_unit = 1000
    #     return result

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            self.price_unit=0.0
            return
        product_tmpl_id = self.env['product.product'].search([('id','=',self.product_id.id)])
        self.price_unit = product_tmpl_id.standard_price


#     @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity','invoice_lines.price_unit','invoice_lines.discount')
#     def _get_invoice_qty(self):
#         super(SaleOrderLine,self)._get_invoice_qty()
#         for line in self:
#             if (line.qty_invoiced):
#                 line.write({'product_uom_qty':line.qty_invoiced})
#             if (line.invoice_lines):
#                 line.write({'price_unit':line.invoice_lines[0].price_unit})
#             if (line.invoice_lines):
#                 line.write({'discount':line.invoice_lines[0].discount})

# class PurchaseOrderLine(models.Model):
#     _inherit = 'purchase.order.line'

#     @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity','invoice_lines.price_unit','invoice_lines.discount')
#     def _compute_qty_invoiced(self):
#         super(PurchaseOrderLine,self)._compute_qty_invoiced()
#         for line in self:
#             if (line.qty_invoiced):
#                 line.write({'product_qty':line.invoice_lines[0].quantity})
#             if (line.invoice_lines):
#                 line.write({'price_unit':line.invoice_lines[0].price_unit})
#             if (line.invoice_lines):
#                 line.write({'discount':line.invoice_lines[0].discount})


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    product_info = fields.Text(string="Комплектация")

class AccountInvoice (models.Model):
    _inherit='account.invoice'
     
    description = fields.Text(
        string='Комментарий',
    )
    # Calculated field 
    amount_paid = fields.Float(
        string=u'Сумма оплат',
        compute='_compute_amount_paid',
        store=True,
    )

    @api.depends('residual')
    def _compute_amount_paid(self):
        for rec in self:
            rec.amount_paid = rec.amount_untaxed-rec.residual


    # state_prepaid = fields.Selection([
    #         ('draft','Черновик'),
    #         ('open', 'Окрыт'),
    #         ('prepaid','Предоплата'),
    #         ('paid', 'Оплачен'),
    #         ('cancel', 'Отменён'),
    #     ], string='Состояние счета', readonly=True, default='draft',
    #     compute='_compute_state_prepaid'
    #     )
    
    state_prepaid = fields.Char(
        string=u'Состояние счета', readonly=True,
        compute='_compute_state_prepaid',
        store=True,
    )



    def action_invoice_open(self):
        super(AccountInvoice,self).action_invoice_open()
        action = self.env.ref('account.action_account_invoice_payment').read()[0]   
        return action

    
    @api.depends('residual','state','amount_paid')
    def _compute_state_prepaid(self):
        state_prepaid_dictionary={'draft':'Черновик','open': 'Окрыт', 'prepaid':'Предоплата','paid':'Оплачен','cancel':'Отменён'}

        for rec in self:
            rec.state_prepaid = state_prepaid_dictionary[rec.state]
            if (rec.residual != rec.amount_total) and (rec.state=='open'):
                rec.state_prepaid=state_prepaid_dictionary['prepaid']
            elif (rec.residual == rec.amount_total) and (rec.state == 'open'):
                rec.state_prepaid=state_prepaid_dictionary['open']
            else:
                pass