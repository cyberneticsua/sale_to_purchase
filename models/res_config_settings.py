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

class ResConfigSettingsCall(models.TransientModel):
    _inherit = 'res.config.settings'

    my_base_call_center_team = fields.Char(
        string="Название команди Call Center",
        help="Указание команди Call Center для поиска менеджера при конвертации создании лида")
    
    def get_values(self):
        res = super(ResConfigSettingsCall, self).get_values()
        res.update(
            my_base_call_center_team=self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_call_center_team')
        )
        return res

    def set_values(self):
        super(ResConfigSettingsCall, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('sale_to_purchase.my_base_call_center_team', self.my_base_call_center_team)

class ResConfigSettingsDefaultActivity(models.TransientModel):
    _inherit = 'res.config.settings'

    my_base_default_activity = fields.Char(
        string="Название базовой задачи",
        help="Указание базовой задачи для менеджера при создании лида и конвертации лида")
    
    def get_values(self):
        res = super(ResConfigSettingsDefaultActivity, self).get_values()
        res.update(
            my_base_default_activity=self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_default_activity')
        )
        return res

    def set_values(self):
        super(ResConfigSettingsDefaultActivity, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('sale_to_purchase.my_base_default_activity', self.my_base_default_activity)

class ResConfigSettingsDefaultPurchaseManagerEmail(models.TransientModel):
    _inherit = 'res.config.settings'

    my_base_default_purch_manager_email = fields.Char(
        string="Email менеджера по закупкам",
        help="Указание email для менеджера по закупкам")
    
    def get_values(self):
        res = super(ResConfigSettingsDefaultPurchaseManagerEmail, self).get_values()
        res.update(
            my_base_default_purch_manager_email=self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_default_purch_manager_email')
        )
        return res

    def set_values(self):
        super(ResConfigSettingsDefaultPurchaseManagerEmail, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('sale_to_purchase.my_base_default_purch_manager_email', self.my_base_default_purch_manager_email)
    
class ResConfigSettingsDefaultActivityUser(models.TransientModel):
    _inherit = 'res.config.settings'

    my_base_default_activity_user = fields.Char(
        string="Default acitivity user login",
        help="Login юзера, которому ставится задача, если для документа нет отвественного")
    
    def get_values(self):
        res = super(ResConfigSettingsDefaultActivityUser, self).get_values()
        res.update(
            my_base_default_activity_user=self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_default_activity_user')
        )
        return res

    def set_values(self):
        super(ResConfigSettingsDefaultActivityUser, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('sale_to_purchase.my_base_default_activity_user', self.my_base_default_activity_user)