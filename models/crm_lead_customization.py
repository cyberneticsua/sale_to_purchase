from odoo import models, fields, api
import logging
from odoo.exceptions import Warning
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from odoo.tools.safe_eval import safe_eval
from random import randint, shuffle
from odoo.exceptions import Warning
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
import math
import pytz
_logger = logging.getLogger(__name__)

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class CrmLeadFields (models.Model):
    _inherit=['crm.lead']

    client_lang= fields.Selection(_lang_get, string='Язык', default=lambda self: self.env.lang,
                            help="If the selected language is loaded in the system, all documents related to "
                                 "this contact will be printed in this language. If not, it will be English.")

    
    convertion_user = fields.Many2one(
        string=u'Кем преобразовано',
        comodel_name='res.users',
    )
    
    # метод, що призначає оперетора Call Center при створенні ліда
    # @api.multi
    # def write(self,vals):
    #     super(CrmLeadFields,self).write(vals)
    #     if self.env.context.get('SaleToPurcahseLoopBreaker'): 
    #         return 
    #     self = self.with_context(SaleToPurcahseLoopBreaker=True) 
    #     if not(self.user_id) and (self.type=='lead'):
    #         my_team = self.env['crm.team'].search([('name', '=', self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_call_center_team'))])
    #         self.env['crm.team'].custom_assign_leads_to_salesman(team_id=my_team.id,lead_id=self.id)

    @api.model
    def create(self, vals):
        ff = super(CrmLeadFields,self).create(vals)
        if not ff.user_id:
            ###25.12.2018
            my_client_type = self.env['client.type'].search([('id','=',ff.client_type_id.id)])
            if my_client_type.name == 'Себе домой (розничн.клиент)' or  my_client_type.name == 'Другое (указать в коммент.)':
                my_team = self.env['crm.team'].search([('name', '=', self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_call_center_team'))])
            else:
                my_team = self.env['crm.team'].search([('name', '=', self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_sales_team'))])
            ###вибір команди
            # my_team = self.env['crm.team'].search([('name', '=', self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_call_center_team'))])
            self.env['crm.team'].custom_assign_leads_to_salesman(team_id=my_team.id,lead_id=ff.id)
            ff._create_action_for_lead(use_default_deadline=False)

        return ff


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
        # 25.12.2018 при конвертації ліда в опортуніті не присвоюємо тім   
        # my_team = self.env['crm.team'].search([('name', '=', self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_sales_team'))])
        # 
        # self.env['crm.team'].custom_assign_leads_to_salesman(team_id=my_team.id,lead_id=self.id)

        # if user_ids:
        #     leads_to_allocate.allocate_salesman(user_ids, team_id=(vals.get('team_id')))

        return res

    #метод, що повертає дані для створення партнера
    @api.multi
    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        my_result = super(CrmLeadFields, self)._create_lead_partner_data(name,is_company,parent_id)
        if self.client_language:
            my_result['client_language']=self.client_language
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
        
        #Перевірка наявності телефону, імя, мови і типу клієнта
        list_of_params = ""
        if not(self.contact_name):
            list_of_params+='имя '
        
        if not(self.phone) and not(self.mobile):
            list_of_params+='телефон '
        else:
            values.update({'phone':self.phone})

        if not(self.client_type_id):
            list_of_params+='тип клиента '
        
        if not(self.client_language):
            list_of_params+='язык клиента '
        
        if list_of_params:
            error_message = "Нужно определить {}".format(list_of_params)
            raise ValidationError(error_message)

        _logger.info('My vals {}'.format(vals))
        _logger.info('My values  {}'.format(values))
        
        self.update({'convertion_user':self.user_id.id})
        self._convert_opportunity(values)

        self._create_action_for_lead(use_default_deadline=True)
        return leads[0].redirect_opportunity_view()

    #generate activity for lead
    def _create_action_for_lead(self, use_default_deadline=True):
        my_activity_type = self.env['mail.activity.type'].search([('name', '=', self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_default_activity'))])
        data1 = self.env['ir.model'].search([('model', '=', 'crm.lead')])
        
        act_vals={
                    'activity_type_id':my_activity_type.id,
                    # 'date_deadline':date_deadline.strftime('%Y-%m-%d'),
                    'summary':my_activity_type.summary,
                    'res_id':self.id,
                    'res_model_id':data1.id,
                }
        if self.user_id.id:
            act_vals['user_id']=self.user_id.id
        else:
            act_vals['user_id']=self.env['res.users'].search([('login','=',self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.my_base_default_activity_user'))]).id
        my_activity = self.env['mail.activity'].create(act_vals)
        my_activity._onchange_activity_type_id()

        t = date.today()
        if (use_default_deadline):
            date_deadline = datetime.now(pytz.timezone(self.user_id.tz or 'GMT')) + timedelta(days=my_activity_type.days)
        else:
            date_deadline = datetime.now(pytz.timezone(self.user_id.tz or 'GMT'))

        my_datetime= datetime.datetime.now()
        if date_deadline.weekday()==5:
            date_deadline = date_deadline + timedelta(days=2)
            my_datetime = my_datetime + timedelta(days=2)
        if date_deadline.weekday()==6:
            date_deadline= date_deadline+ timedelta(days=1)
            my_datetime = my_datetime + timedelta(days=1)
        
        # my_datetime= datetime.datetime.now()       
        my_activity.write({
                            'date_deadline':date_deadline.strftime('%Y-%m-%d'),
                            'datetime_deadline':my_datetime.strftime('%Y-%m-%d %H:%M:%S')
                        })
       

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

        #fields for utm.referrer and utm.expid
    utm_referrer_id = fields.Many2one('utm.referrer', 'Referrer',
                                help="This is the referrer of the link")
    utm_expid_id = fields.Many2one('utm.expid', 'Expid',
                                help="This is the expid of the link")
    utm_term_id = fields.Many2one('utm.term', 'Term',
                                help="This is the term of the link")
    utm_content_id = fields.Many2one('utm.content', 'Content',
                                help="This is the content of the link")
    utm_position_id = fields.Many2one('utm.position', 'Position',
                                help="This is the position of the link")
    utm_matchtype_id = fields.Many2one('utm.matchtype', 'Matchtype',
                                help="This is the matchtype of the link")
    utm_network_id = fields.Many2one('utm.network', 'Network',
                                help="This is the network of the link")
    lead_furniture_type_from_mail=fields.Char(string="Интересующий тип мебели")
    lead_quantity_from_mail=fields.Char(string="Желаемое количество посадочных мест")                                
    lead_date_from_mail=fields.Char(string="Желаемая дата поставки")
    lead_additional_from_mail = fields.Char(string="Комментарии Клиента")
    sent_from_page = fields.Char(string="Отправлено со страницы")

    @api.multi
    def action_open_new_tab(self):
        # for rec in self:
        # my_lead_action = self.env['ir.actions.act_window'].search([('id', '=', self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.lead_action_name'))])
        # my_oppor_action = self.env['ir.actions.act_window'].search([('id', '=', self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.oppor_action_name'))])

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if (self.type=="lead"):
            record_url = base_url + "/web#id=" + str(self.id) + "&view_type=form&model=&&action="+str(self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.lead_action_name'))
        else:
            record_url = base_url + "/web#id=" + str(self.id) + "&view_type=form&model=&&action="+str(self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.oppor_action_name'))
        client_action = {
                'type': 'ir.actions.act_url',
                'name': "ZZZ",
                'target': 'new',
                'url': record_url,
                }
        return client_action                                

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
