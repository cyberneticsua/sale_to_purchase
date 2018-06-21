from odoo import models, fields, api
from odoo.exceptions import Warning
from odoo.exceptions import UserError

class SaleOrderAutoInvoice (models.Model):
    _inherit="sale.order"

    def action_confirm(self):
        super(SaleOrderAutoInvoice,self).action_confirm()
        payment = self.env['sale.advance.payment.inv'].create({'advance_payment_method': 'all'})
        payment.with_context(active_ids=self.id).create_invoices()        
        invoices = self.mapped('invoice_ids')
        for invoice in invoices:
            invoice.action_invoice_open()