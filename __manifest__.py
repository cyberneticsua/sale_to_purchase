# -*- coding: utf-8 -*-
{
    "name" : "Sale to Purchase order",
    "version" : "1.0",
    'summary': """ This module brings users to create a purchase order while doing sale order.""",
    'category': 'Sales Management',
    'author': 'Igor Vinnychuk',
    'website': '',
    "depends" : ['sale','purchase','crm','mail','base','sales_team','utm_referrer','web_one2many_checkbox','res_partner_client_lang','res_partner_client_type'],
    'data': ['views/sale_order_tab.xml',
             'views/sale_order_inherit.xml',
             'views/sale_order_bom.xml',
             'views/purchase_order_lines.xml',
             'views/purchase_order_inherit.xml',
             'views/product_inherit.xml',
             'views/lead_modification.xml',
             'views/activities_list.xml',
             'data/defaultdata.xml',
             'security/ir.model.access.csv'
             ],
    'images': [],
    'license': 'LGPL-3',
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,

}