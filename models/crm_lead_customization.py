from odoo import models, fields, api
from odoo.exceptions import Warning
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from odoo.tools.safe_eval import safe_eval
from random import randint, shuffle
import math

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class CrmLeadFields (models.Model):
    _inherit=['crm.lead']

    client_lang= fields.Selection(_lang_get, string='Язык', default=lambda self: self.env.lang,
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
        
        leads_to_allocate = leads
        if self._context.get('no_force_assignation'):
            leads_to_allocate = leads_to_allocate.filtered(lambda lead: not lead.user_id)
        
        # Assignment of opportunities to manager
        my_team = self.env['crm.team'].search([('name', '=', self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_sales_team'))])
        
        self.env['crm.team'].custom_assign_leads_to_salesman(team_id=my_team.id,lead_id=self.id)

        # if user_ids:
        #     leads_to_allocate.allocate_salesman(user_ids, team_id=(vals.get('team_id')))

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

        self._create_action_for_lead()
        return leads[0].redirect_opportunity_view()

    #generate activity for lead
    def _create_action_for_lead(self):
        my_activity = self.env['mail.activity.type'].search([('name', '=', 'Call')])
        data1 = self.env['ir.model'].search([('model', '=', 'crm.lead')])
        t= date.today()
        date_deadline = (datetime.now() + timedelta(days=my_activity.days))
        if date_deadline.weekday()==5:
            date_deadline= date_deadline+ timedelta(days=2)
        if date_deadline.weekday()==6:
            date_deadline= date_deadline+ timedelta(days=1)
        act_vals={
                    'activity_type_id':my_activity.id,
                    'date_deadline':date_deadline.strftime('%Y-%m-%d'),
                    'res_id':self.id,
                    'res_model_id':data1.id,
                }
        if self.user_id.id:
            act_vals['user_id']=self.user_id.id
        my_activity = self.env['mail.activity'].create(act_vals)

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
        
        if lead.phone:  # search through the existing partners based on the lead's phone
            partner = Partner.search([('phone', '=', lead.phone)], limit=1)
            return partner.id

        # if lead.partner_name:  # search through the existing partners based on the lead's partner or contact name
        #     partner = Partner.search([('name', 'ilike', '%' + lead.partner_name + '%')], limit=1)
        #     return partner.id

        # if lead.contact_name:
        #     partner = Partner.search([('name', 'ilike', '%' + lead.contact_name+'%')], limit=1)
        #     return partner.id

        return False

class LeadsAllocation(models.Model):
    _inherit=['crm.team']

    @api.model
    def custom_assign_leads_to_salesmen(self, all_team_users, lead_id):
        users = []
        for su in all_team_users:
            if (su.maximum_user_leads - su.leads_count) <= 0:
                continue
            domain = safe_eval(su.team_user_domain or '[]')
            domain.extend([
                ('user_id', '=', False),
                ('assign_date', '=', False),
                ('score', '>=', su.team_id.min_for_assign)
            ])

            # assignation rythm: 2 days of leads if a lot of leads should be assigned
            limit = int(math.ceil(su.maximum_user_leads / 15.0))

            # domain.append(('team_id', '=', su.team_id.id))

            leads = self.env["crm.lead"].search([('id','=',lead_id)])
            users.append({
                "su": su,
                "nbr": min(su.maximum_user_leads - su.leads_count, limit),
                "leads": leads
            })

        assigned = set()
        while users:
            i = 0

            # statistically select the user that should receive the next lead
            idx = randint(0, sum(u['nbr'] for u in users) - 1)

            while idx > users[i]['nbr']:
                idx -= users[i]['nbr']
                i += 1
            user = users[i]

            # Get the first unassigned leads available for this user
            while user['leads'] and user['leads'][0] in assigned:
                user['leads'] = user['leads'][1:]
            if not user['leads']:
                del users[i]
                continue

            # lead convert for this user
            lead = user['leads'][0]
            assigned.add(lead)

            # Assign date will be setted by write function
            data = {'user_id': user['su'].user_id.id}

            # ToDo in master/saas-14: add option mail_auto_subscribe_no_notify on the saleman/saleteam
            lead.with_context(mail_auto_subscribe_no_notify=True).write(data)
            # lead.convert_opportunity(lead.partner_id and lead.partner_id.id or None)
            self._cr.commit()

            user['nbr'] -= 1
            if not user['nbr']:
                del users[i]

    @api.model
    def custom_assign_leads_to_salesman(self,team_id,lead_id):
        leads = self.env["crm.lead"].search([('id','=',lead_id)])
        leads.write({'team_id': team_id})

        all_team_users = self.env['team.user'].search([('running', '=', True),('team_id','=',team_id)])

        self.custom_assign_leads_to_salesmen(all_team_users=all_team_users,lead_id=lead_id)
