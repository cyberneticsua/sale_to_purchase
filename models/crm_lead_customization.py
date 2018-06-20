from odoo import models, fields, api
from odoo.exceptions import Warning
from odoo.exceptions import UserError

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class CrmLeadFields (models.Model):
    _inherit=['crm.lead']

    client_lang= fields.Selection(_lang_get, string='Language', default=lambda self: self.env.lang,
                            help="If the selected language is loaded in the system, all documents related to "
                                 "this contact will be printed in this language. If not, it will be English.")

    @api.model
    def _get_duplicated_leads(self, partner_id, email, include_lost=False):
        """ Search for opportunities that have the same partner and that arent done or cancelled """
        return self.env['crm.lead']._get_duplicated_leads_by_emails(partner_id, email, include_lost=include_lost)

    @api.multi
    def _convert_opportunity(self,vals):
        self.ensure_one()
        res = False
        leads = self.env['crm.lead'].browse(vals.get('lead_ids'))
        for lead in leads:
            self_def_user = self.with_context(default_user_id=self.user_id.id)
            #Detecting partner
            partner_id = self_def_user._create_partner(
                lead.id, vals.get('action'), vals.get('partner_id') or lead.partner_id.id)
            res = lead.convert_opportunity(partner_id, [], False)
        user_ids = vals.get('user_ids')

        leads_to_allocate = leads
        if self._context.get('no_force_assignation'):
            leads_to_allocate = leads_to_allocate.filtered(lambda lead: not lead.user_id)

        if user_ids:
            leads_to_allocate.allocate_salesman(user_ids, team_id=(vals.get('team_id')))

        return res

    #метод, що повертає дані для створення партнера
    @api.multi
    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        my_result = super(CrmLeadFields, self)._create_lead_partner_data(name,is_company,parent_id)
        if self.client_lang:
            my_result['lang']=self.client_lang
            my_result['client_type_id']=self.client_type_id.id
        return my_result


    @api.multi
    def sale_lead2opportunity_waldberg(self,vals):
        """ Convert lead to opportunity or merge lead and opportunity and open
            the freshly created opportunity view.
        """
        self.ensure_one()
        values = {
            'team_id': self.team_id.id,
        }
        
        if self.partner_id:
            values['partner_id'] = self.partner_id.id
        
        values['action'] = 'exist' if self.partner_id else 'exist_or_create'
        leads = self.env['crm.lead'].browse(self.id)
        values.update({'lead_ids': leads.ids, 'user_ids': [self.user_id.id]})
        self._convert_opportunity(values)

        return leads[0].redirect_opportunity_view()

    def _create_partner(self, lead_id, action, partner_id):
        """ Create partner based on action.
            :return dict: dictionary organized as followed: {lead_id: partner_assigned_id}
        """
        #TODO this method in only called by Lead2OpportunityPartner
        #wizard and would probably diserve to be refactored or at least
        #moved to a better place
       
        if action == 'exist_or_create':
            partner_id = self.with_context(active_id=lead_id)._find_matching_partner()
        if not partner_id:
            action = 'create'
        result = self.env['crm.lead'].browse(lead_id).handle_partner_assignation(action, partner_id)
        return result.get(lead_id)
    
    @api.model
    def _find_matching_partner(self):
        """ Try to find a matching partner regarding the active model data, like
            the customer's name, email, phone number, etc.
            :return int partner_id if any, False otherwise
        """
        if not self._context.get('active_id'):
            return False
        lead = self.env['crm.lead'].browse(self._context.get('active_id'))
        
        # find the best matching partner for the active model
        Partner = self.env['res.partner']
        if lead.partner_id:  # a partner is set already
            return lead.partner_id.id

        if lead.email_from:  # search through the existing partners based on the lead's email
            partner = Partner.search([('email', '=', lead.email_from)], limit=1)
            return partner.id

        if lead.partner_name:  # search through the existing partners based on the lead's partner or contact name
            partner = Partner.search([('name', 'ilike', '%' + lead.partner_name + '%')], limit=1)
            return partner.id

        if lead.contact_name:
            partner = Partner.search([('name', 'ilike', '%' + lead.contact_name+'%')], limit=1)
            return partner.id

        return False