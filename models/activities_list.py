# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ActivityTypeList(models.Model):
    _inherit = ['mail.activity']

    
    @api.multi
    def action_open_new_tab(self):
        for rec in self:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            record_url = base_url + "/web#id=" + str(self.id) + "&view_type=form&model=&&action="+str(self.env['ir.config_parameter'].sudo().get_param('sale_to_purchase.activity_action_id'))

        client_action = {
                'type': 'ir.actions.act_url',
                'name': "ZZZ",
                'target': 'new',
                'url': record_url,
                }
        return client_action
    
    # def return_values(self):
    #     return {
    #          'type': 'ir.actions.act_window',
    #          'res_model': self.res_model,
    #          'res_id':self.res_id,
    #          'view_type': 'form',
    #          'view_mode': 'form',
    #          'target': 'main',
    #          'view_id':False,
    #      }

class DuplicatesLead(models.Model):
    #########Підрахунок кількості дублікатів 
    _inherit=['crm.lead']

    duplicates_count= fields.Integer(
        string='Количество дубликатов',compute='count_duplicate_leads'
    )
    
    def count_duplicate_leads(self):
        self.duplicates_count = self.env['crm.lead'].search_count(['&','|',
            '&',('email_from','!=',False),('email_from', '=', self.email_from),
            '&',('phone', '!=',False),('phone', '=', self.phone),
            ('id','!=',self.id)
        ])
 
    @api.model
    def get_lead_view(self, view_title):
        action = self.env.ref('crm.crm_lead_opportunities_tree_view').read()[0]
        user_team_id = self.env.user.sale_team_id.id
        if not user_team_id:
            user_team_id = self.search([], limit=1).id
            action['help'] = """<p class='oe_view_nocontent_create'>Click here to add new opportunities</p><p>
    Looks like you are not a member of a sales team. You should add yourself
    as a member of one of the sales team.
</p>"""
            if user_team_id:
                action['help'] += "<p>As you don't belong to any sales team, Odoo opens the first one by default.</p>"

        action_context = self._context.copy()
        if user_team_id:
            action_context['default_team_id'] = user_team_id
        
        child_ids = self.env['crm.lead'].search(['&','|',
            '&',('email_from','!=',False),('email_from', '=', self.email_from),
            '&',('phone', '!=',False),('phone', '=', self.phone),
            ('id','!=',self.id)
        ])

        action['domain'] = [
        #         # ('state', 'in', order_states),
        #         # ('partner_id', 'in', partner_ids),
                ('id', 'in', child_ids.ids),
            ]
        action['name']=view_title
        tree_view_id = self.env.ref('crm.crm_case_tree_view_leads').id
        form_view_id = self.env.ref('crm.crm_case_form_view_leads').id
        kanb_view_id = self.env.ref('crm.crm_case_kanban_view_leads').id
        action['views'] = [
                [tree_view_id, 'tree'],
                [kanb_view_id, 'kanban'],
                [form_view_id, 'form'],
                [False, 'graph'],
                [False, 'calendar'],
                [False, 'pivot']
            ]
        action['context'] = action_context
        return action


    @api.multi
    def button_lead_duplicates(self):
        return self.get_lead_view("Список возможных дубликатов")

class DuplicatesLeadPartner(models.Model):
    #########Підрахунок кількості дублікатів 
    _inherit=['crm.lead']

    partner_duplicates_count= fields.Integer(
        string='Количество партн.дубликатов',compute='count_duplicate_partner_leads'
    )
    
    def count_duplicate_partner_leads(self):
        self.partner_duplicates_count = self.env['res.partner'].search_count(['|',
            '&',('email','!=',False),('email', '=', self.email_from),
            '&',('phone', '!=',False),('phone', '=', self.phone),
            
        ])
 

    @api.multi
    def button_lead_partner_duplicates(self):
        return self.get_partner_view("Список возможных дубликатов клиентов")

    @api.model
    def get_partner_view(self, view_title):
        ir_model_data = self.env['ir.model.data']
        try:
           tree_id = ir_model_data.get_object_reference('base', 'view_partner_tree')[1]
           form_id = ir_model_data.get_object_reference('base', 'view_partner_form')[1]
        except ValueError:
           view_id = False
        # child_ids = self.env['res.partner'].search(['|','|',
        #     '&',('email','!=',False),('email', '=', self.email_from),
        #     '&',('phone', '!=',False),('phone', '=', self.phone),
        #     '&',('phone', '!=',False),('mobile', '=', self.phone),
        # ])
        child_ids = self.env['res.partner'].search(['|',
            '&',('email','!=',False),('email', '=', self.email_from),
            '&',('phone', '!=',False),('phone', '=', self.phone),
            
        ])
        action_context = self._context.copy()
        return {
            'name': view_title,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', child_ids.ids)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'view_id': False,
            'views': [(tree_id, 'tree'),(form_id, 'form')],
            'target': 'current',
            'context': action_context,
        }


        