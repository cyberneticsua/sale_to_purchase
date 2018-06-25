# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ActivityTypeList(models.Model):
    _inherit = ['mail.activity']

    
    def return_values(self):
        return {
             'type': 'ir.actions.act_window',
             'res_model': self.res_model,
             'res_id':self.res_id,
             'view_type': 'form',
             'view_mode': 'form',
             'target': 'main',
             'view_id':False,
         }

class DuplicatesLead(models.Model):
    #########Підрахунок кількості деталей для замовлення 
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
        tree_view_id = self.env.ref('crm.crm_case_tree_view_oppor').id
        form_view_id = self.env.ref('crm.crm_case_form_view_oppor').id
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
