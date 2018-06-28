# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    my_base_sales_team = fields.Char(
        string="Название команди продаж",
        help="Указание команди прожаж для поиска менеджера при конвертации лида в сделку")
    
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            my_base_sales_team=self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_sales_team')
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('sale_to_purchase.my_base_sales_team', self.my_base_sales_team)
