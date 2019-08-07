from odoo import models, fields, api
from odoo.exceptions import Warning
from odoo.exceptions import UserError

class MailWaldberg(models.Model):
    _inherit = "mail.message" 
    
    # @api.multi
    # def create(self,vals):
    #     super(PRTMailMessage,self).create(vals)
    #     self.mark_as_unread_waldberg()
    
    
    @api.depends('partner_ids')
    @api.multi
    def mark_as_unread_waldberg(self, channel_ids=None):
        """ Add needactions to messages for the current partner. """
        
        # partner_id = self.env.user.partner_id.id
        # for message in self:
        #     message.write({'needaction_partner_ids': [(4, partner_id)]})



        # recipients_allowed = self.env['res.partner']
        # for rec in self:
        #     for partner in rec.partner_ids:
        #         try:
        #             # partner.check_access_rule('read')
        #             recipients_allowed += partner
        #         except:
        #             continue
        user_ids = []
        for rec in self:
            for partner in rec.partner_ids:
                user_ids.append(self.env["res.users"].search([("partner_id", "=", partner.id)]).id)
       
        # for message in self:
        #     message.write({'needaction_partner_ids': [(4, recipients_allowed)]})
        # user_ids=self.env["res.users"]
        # for rec in recipients_allowed:
        #     s = self.env["res.users"].search([("partner_id", "=", rec.id)])
        #     if s:
        #         user_ids+=s

        ids = [m.id for m in self]
        notification = {'type': 'mark_as_unread', 'message_ids': ids, 'channel_ids': channel_ids}
        self.env['bus.bus'].sendone((self._cr.dbname, 'res.partner', user_ids[0]), notification)