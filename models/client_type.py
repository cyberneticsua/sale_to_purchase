from odoo import api, fields, models

class ClientType(models.Model):
    _name = 'client.type'

    name = fields.Char('Тип лида/клиента', required=True)
    description = fields.Text('Описание', translate=True)
    
class PartnerTypeLead(models.Model):
    _inherit = 'crm.lead'

    client_type_id = fields.Many2one(
        'client.type',
        string='Тип лида/клиента',
        help='Select a type for this client'
    )