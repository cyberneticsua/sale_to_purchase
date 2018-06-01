from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import Warning
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class SaleOrderLine (models.Model):
    _inherit="sale.order.line"    
    
    purchase_status = fields.Selection(
        [('not_purchased','К заказу'),
            ('created','Создано заказ'),
            ('purchased', 'Заказано'),
            ('ready_for_delivery', 'Готово к отправке'),
            ('delivering', 'В дороге'),
            ('done', 'Доставлено'),],
        string='Состояние',default='not_purchased')
    
    product_info = fields.Text(string="Базовая комплектация")
    
    @api.onchange('product_id')
    def _get_product_info(self):
        product_template_id = self.env['product.product'].search([('id','=',self.product_id.id)])
        product_info_base = self.env['product.template'].search([('id','=',product_template_id.product_tmpl_id.id)])
        self.product_info=product_info_base.base_params_info

class PurchaseOrderLine (models.Model):
    _inherit='purchase.order.line'
    real_ready_date=fields.Datetime(
        string="Реал. дата"
    )
    description = fields.Text(
        string="Детали"
    )
    purchase_status = fields.Selection(
        [   ('created','Создано заказ'),
            ('purchased', 'Заказано'),
            ('ready_for_delivery', 'Готово к отправке'),
            ('delivering', 'В дороге'),
            ('done', 'Доставлено'),],
        string='Состояние',default='created')
    product_info = fields.Text(string="Комплектация")

class PurchaseOrder (models.Model):
    _inherit='purchase.order'

    # 24.04.2018
    prepayment = fields.Char(
        string='Предолата',
    )

    prepayment_date = fields.Date(
        string='Дата предоплаты',
    )

    sale_order_id = fields.Many2one(
        string='Заказ клиента',
        comodel_name='sale.order',
    )

class SaleToPurchase(models.Model):
    _inherit = 'sale.order'
    
    purchase_order_ids =fields.One2many(
        string='Заказ на покупку',
        comodel_name='purchase.order',
        inverse_name='sale_order_id',
    )
    
    purchase_order_count = fields.Integer(compute='_purchase_order_count', string='# of Purchase Order')

    client_type = fields.Selection(
        [('designer','Дизайнер/архитектор/дизайнер.бюро'),
            ('home','Себе домой (розничн.клиент)'),
            ('restaurant', 'Ресторан'),
            ('cafe', 'Кафе'),
            ('bar', 'Бар'),
            ('hotel', 'Гостиница'),
            ('partner', 'Партнёр (посредник)'),
            ('distributor', 'Дистрибьютор'),
            ('eshop', 'Интернет-магазин'),
            ('retail', 'Розничный магазин'),
            ('candidate', 'Соискатель'),
            ('other', 'Другое (указать в коммент.)'),
            ],
        string='Тип клиента',default='designer', required='True')
   
   
   
    # @api.multi
    # def action_confirm(self):
    #     super(SaleToPurchase, self).action_confirm()
    #     # raise Warning (self.partner_id.id)
    #     self.name=self.partner_id.name
    #     return True

    @api.model
    def create(self, vals):
        partner=self.env['res.partner'].browse(vals.get('partner_id'))
        vals['name']=partner.name
        result = super(SaleToPurchase,self).create(vals)
        return result
   
    @api.multi
    def _purchase_order_count(self):
        PurchaseOrder = self.env['purchase.order']
        self.purchase_order_count = PurchaseOrder.search_count([('sale_order_id', '=', self.id)])


    @api.multi
    def action_purchase_orders(self):
        view_id = self.env.ref('sale_to_purchase.wizard_form_purchase_order').id
        context = self._context.copy()
        context['sale_order_id']=self.id
        context['sale_order_partner_id']=self.partner_id.name
        return {
            'name':'Purchase Order',
            'view_type':'form',
            'view_mode':'form',
            'views' : [(view_id,'form')],
            'res_model':'purchase.order.wizard',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'target':'new',
            'context':context,
        }
    
    @api.multi
    def get_purchase_orders_view(self, view_title):
        orders = self.env['purchase.order'].search([
            ('sale_order_id', '=', self.id),
        ])
        # res = self.env.ref('purchase.purchase_order_tree').read()[0]

        tree_view_id = self.env.ref('purchase.purchase_order_tree').id
        # form_view_id = self.env.ref('purchase.purchase_order_form').id
        res ['name']= view_title
        res['type']= 'ir.actions.act_window'
        res['res_model']= 'purchase.order'
        res['view_type']= 'form'
        res['view_id']=tree_view_id
        
        # res['views']=
        # [
        #     [tree_view_id, 'tree'],
        #     [form_view_id, 'form'],
        # ]

        if len(orders) == 1:
            res['res_id'] = orders[0].id
            res['view_mode'] = 'form'
        else:
            res['domain'] = [
                ('sale_order_id', '=', self.id),
            ]
        res['view_mode'] = 'tree,form'

        return res
    
    #статус замовлення для відображення в списку
    sale_order_status_field = fields.Boolean("Заказ выполнен", 
    default=False,
    )

         
class PurchaseOrderWizard(models.TransientModel):
    _name= 'purchase.order.wizard'
    _description = 'Purchase Order wizard'
    
    partner_id = fields.Many2one('res.partner', string='Поставщик',required=True)
    order_line=fields.One2many('purchase.order.line.wizard', 'wizard_order_id', string='Order Lines')
    date_order = fields.Datetime(string='Дата готовности',required=True)
    # company_id = fields.Many2one('res.company', string='Company')
    # picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To')
    
    @api.multi
    @api.onchange('partner_id')
    def _compute_price(self):
        for i in self.order_line:
            product_tmpl_id = self.env['product.product'].search([('id','=',i.product_id.id)])
            product_price_from_supplier = self.env['product.supplierinfo'].search([('product_tmpl_id','=',product_tmpl_id.product_tmpl_id.id),('name','=',self.partner_id.id)])
            if product_price_from_supplier:
                i.price_unit=product_price_from_supplier.price
            else:
                i.price_unit=0.0
    
    @api.multi
    def generate_purchase_order(self):
        
        orderline_pooler=self.env['purchase.order.line']
        purchase_pooler=self.env['purchase.order']
        context = self._context.copy()
        purch_order_count_for_name=purchase_pooler.search_count([('sale_order_id', '=', context['sale_order_id'])])
        purchase_order_name = context['sale_order_partner_id'] + "-"+str(purch_order_count_for_name+1)
        pur_id=purchase_pooler.create({'partner_id':self.partner_id.id,
                                       'sale_order_id':context['sale_order_id'],
                                       'name':purchase_order_name,
                                    #    'date_order':fields.Datetime.now,
                                       
#                                 'currency_id':self.currency_id,
#                                 'order_line':[(6,0,[line_ids])]
                                })
        for i in self.order_line:
            data= self.env['sale.order.line'].search([('id', '=', i.sale_order_line_id)])
            
            line_ids=orderline_pooler.create({'product_id':i.product_id.id,
                                                'name':i.name,
                                                'product_qty':i.product_qty,
                                                'product_info':i.product_info,
                                                # 'price_unit':i.price_unit,
                                                'price_unit':i.price_unit,
                                                'product_uom':1,
                                                'order_id':pur_id.id,
                                                'date_planned':self.date_order,
                                                #додано посилання на sale.order.line
                                                'sale_order_line_id':data.id,
                                                })
            
            # data= self.env['sale.order.line'].search([('id', '=', i.sale_order_line_id.id)])
            data.sudo().write ({'purchase_status':'created'})
                                                
        pur_id.button_confirm()
    
    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrderWizard, self).default_get(fields)
        context=self._context
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
                result1.append((0, 0, {'product_id': item.product_id.id,
                                    'name':item.name,
                                    'product_qty':item.product_uom_qty,
                                    # 'price_unit':item.price_unit,
                                    'product_info':item.product_info,
                                    'price_unit':0.0,
                                    'product_uom':item.product_uom.id,
                                    # 'price_subtotal':item.price_unit*item.product_uom_qty,
                                    'price_subtotal':0.0*item.product_uom_qty,
                                    ###################################
                                    'sale_order_line_id':item.id,
                                   }))
        res.update({'order_line': result1})   
        return res
    
class PurchaseOrderLineWizard(models.TransientModel):
    _name = 'purchase.order.line.wizard'
    _description = 'Purchase Order Line wizard'

    
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

    
    name = fields.Text(string='Описание')
    wizard_order_id=fields.Many2one('purchase.order.wizard')
    product_id = fields.Many2one('product.product', string='Продукция')
    product_info=fields.Text(string='Базовая комплектация')
    product_qty = fields.Float(string='Кол-во', digits=dp.get_precision('Product Unit of Measure'))
    price_unit = fields.Float(string='Цена', digits=dp.get_precision('Product Price'))
    product_uom = fields.Many2one('product.uom', string='Ед.измер.')
    price_subtotal = fields.Float(compute='_compute_amount',string='Подытог')
    sale_order_line_id = fields.Integer(
        string='Sale Order Line ID',
    )

class ProductTemplateInfo(models.Model):
    _inherit="product.template"
    base_params_info=fields.Text(string="Базовая комплектация")