from odoo import api, fields, models

class ClientType(models.Model):
    _name = 'client.type'

    name = fields.Char('Тип лида/клиента', required=True)
    description = fields.Text('Описание', translate=True)
    
    # res_partner_ids = fields.One2many(
    #     'res.partner',
    #     'client_type_id',
    #     string='Client Types',
    # )
    # partners_count = fields.Integer(
    #     string='Количество лидов/клиентов',
    #     compute='_get_partner_count',
    # )

    # @api.one
    # @api.depends('res_partner_ids')
    # def _get_partner_count(self):
    #     self.partners_count = len(self.res_partner_ids)


# class PartnerType(models.Model):
#     _inherit = 'res.partner'

    
    # client_type_id = fields.Many2one(
    #     'client.type',
    #     string='Тип лида/клиента',
    #     help='Select a type for this client'
    # )

class PartnerTypeLead(models.Model):
    _inherit = 'crm.lead'

    client_type_id = fields.Many2one(
        'client.type',
        string='Тип лида/клиента',
        help='Select a type for this client'
    )