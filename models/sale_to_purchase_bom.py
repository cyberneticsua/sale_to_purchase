from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import Warning
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
# from openerp.tools import float_is_zero

class SaleToPurchase(models.Model):
    _inherit = 'sale.order'
    
    @api.multi
    def action_purchase_orders_bom(self):
        view_id = self.env.ref('sale_to_purchase.wizard_form_purchase_order_bom').id
        context = self._context.copy()
        context['sale_order_id']=self.id
        context['sale_order_partner_id']=self.partner_id.name
        return {
            'name':'Purchase Order',
            'view_type':'form',
            'view_mode':'form',
            'views' : [(view_id,'form')],
            'res_model':'purchase.order.bom.wizard',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'target':'new',
            'context':context,
        }
    
         
class PurchaseOrderBOMWizard(models.TransientModel):
    _name= 'purchase.order.bom.wizard'
    _description = 'Purchase Order BOM wizard'
    
   
    order_line=fields.One2many('purchase.order.line.bom.wizard', 'wizard_order_id', string='Order Lines')
    # date_order = fields.Date(string='Дата готовности',required=True)
    company_id = fields.Many2one('res.company', string='Company')
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To')
    # sale_order_line_id = fields.Integer(
    #     string='Sale Order Line ID',
    # )
    

    @api.multi
    def generate_purchase_order_bom(self):
        context = self._context.copy()
        

        vendor_ids = []
        sale_order_lines_ids = []
        for i in self.order_line:
            if i.partner_id.id not in vendor_ids:
                vendor_ids.append(i.partner_id.id)
            if i.sale_order_line_id not in sale_order_lines_ids:
                sale_order_lines_ids.append(i.sale_order_line_id)
        
        for s in sale_order_lines_ids:
            data= self.env['sale.order.line'].search([('id', '=', s)])
            data.sudo().write ({'purchase_status':'created'})


        for v in vendor_ids:
            orderline_pooler=self.env['purchase.order.line']
            purchase_pooler=self.env['purchase.order']
            purch_order_count_for_name=purchase_pooler.search_count([('sale_order_id', '=', context['sale_order_id'])])
            purchase_order_name = context['sale_order_partner_id'] + "-"  +str(purch_order_count_for_name+1)
            pur_id=purchase_pooler.create({'partner_id':v,
                                       'sale_order_id':context['sale_order_id'],
                                       'name':purchase_order_name,
                                 })
            
            for i in self.order_line:
                if i.partner_id.id == v:
                    data= self.env['sale.order.line'].search([('id', '=', i.sale_order_line_id)])
                    line_ids=orderline_pooler.create({'product_id':i.product_id.id,
                                                'name':i.name,
                                                'product_qty':i.product_qty,
                                                'price_unit':i.price_unit,
                                                'product_uom':i.product_uom.id,
                                                'order_id':pur_id.id,
                                                #'date_planned':self.date_order,
                                                'date_planned':i.date_planned,
                                                #додавання посилання на sale order
                                                'sale_order_line_id':data.id,
                                                #25.12.2018 додавання комплектації товару
                                                'product_info':i.product_info,
                                                })
            pur_id.button_confirm()
    
    def _compute_price(self, product_id):
        product_tmpl_id = self.env['product.product'].search([('id','=',product_id)])
        return product_tmpl_id.standard_price

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrderBOMWizard, self).default_get(fields)
        context = self._context.copy()
        error_message = "Нужно определить одну строку"
        record=self.env['sale.order'].search([('id','=',context['active_id'])])
        result1=[]
        subtotal=0

        if 'o2m_selection' not in context:
            raise ValidationError(error_message)
        selection = context['o2m_selection']
        
        if 'order_line' not in selection:
            raise ValidationError(error_message)
        line_selection = selection['order_line']
        
        selected_ids = line_selection['ids']

        for item in record.order_line:
            if item.id in selected_ids:
                product_tmpl_id = self.env['product.product'].search([('id','=',item.product_id.id)])
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id','=',product_tmpl_id.product_tmpl_id.id)])
                if bom_id:
                    bom_lines_ids = self.env['mrp.bom.line'].search([('bom_id','=',bom_id.id)])
                    if bom_lines_ids:
                        for bom_item in bom_lines_ids:
                            price_price=self._compute_price(bom_item.product_id.id)
                            result1.append((0, 0, {'product_id': bom_item.product_id.id,
                                    'name':bom_item.product_id.name,
                                    'product_qty':bom_item.product_qty*item.product_uom_qty,
                                    'price_unit':price_price,
                                    'product_uom':bom_item.product_uom_id.id,
                                    'price_subtotal':price_price*bom_item.product_qty*item.product_uom_qty,
                                    ###################################
                                    'sale_order_line_id':item.id,
                                   }))
        res.update({'order_line': result1})   
        return res
    
class PurchaseOrderLineWizard(models.TransientModel):
    _name = 'purchase.order.line.bom.wizard'
    _description = 'Purchase Order Line BOM wizard'



    # Розрахунок ціни з використанням вендорапостачальника
    # @api.multi
    # # @api.onchange('partner_id')
    # def _compute_price(self):
        # product_tmpl_id = self.env['product.product'].search([('id','=',self.product_id.id)])
        # product_price_from_supplier = self.env['product.supplierinfo'].search([('product_tmpl_id','=',product_tmpl_id.product_tmpl_id.id),('name','=',self.partner_id.id)])
        # if product_price_from_supplier:
            # self.price_unit=product_price_from_supplier.price
        # else:
            # self.price_unit=product_tmpl_id.standard_price
        # self.price_unit=product_tmpl_id.standard_price
    
    @api.multi
    @api.depends('product_qty','price_unit')
    def _compute_amount(self):
        for record in self:
            record.price_subtotal=record.product_qty*record.price_unit
    
    @api.multi
    @api.onchange('product_id')
    def _add_name(self):
        product_tmpl_id = self.env['product.product'].search([('id','=',self.product_id.id)])
        self.name = product_tmpl_id.name
        self.product_uom = product_tmpl_id.uom_id
        
    
    name = fields.Text(string='Описание')
    wizard_order_id=fields.Many2one('purchase.order.bom.wizard')
    product_id = fields.Many2one('product.product', string='Продукция')
    product_qty = fields.Float(string='Кол-во', digits=dp.get_precision('Product Unit of Measure'))
    price_unit = fields.Float(string='Цена', digits=dp.get_precision('Product Price'))
    product_uom = fields.Many2one('product.uom', string='Ед.измер.')
    price_subtotal = fields.Float(compute='_compute_amount',string='Подытог')
    partner_id = fields.Many2one('res.partner', string='Поставщик',required=True)
    sale_order_line_id = fields.Integer(
        string='Sale Order Line ID',
    )

    date_planned=fields.Date(string='Дата готовности')

    #25.12.2018
    product_info=fields.Text(string='Комплектация')
