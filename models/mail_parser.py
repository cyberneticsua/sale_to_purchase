from odoo import models, fields, api
from odoo.exceptions import Warning

class MyMailParser(models.Model):
    _inherit= ['crm.lead']
    
    @api.model
    def create(self, vals):
        partner=self.env['res.partner'].browse(vals.get('partner_id'))
        vals['name']=partner.name
        result = super(SaleToPurchase,self).create(vals)
        return result

    def message_new(self, msg_dict, custom_values):
        """ Overrides crm_lead message_new 
        """
        self = self.with_context(default_user_id=False)
        
        #Извлечение тела письма
        description=msg_dict.get('body')
        #parsing
        # _dict=_parse_description(description)
        fields=['Name','Email','Phone']
        _dict={}
		# description=description.lower()
        for field in fields:
            index = description.find(field)
            if (index>0):
                _dict[field]=description[index:index+10]
        
        if custom_values is None:
            custom_values = {}
        defaults = {
        	'phone':_dict.get('Phone'),
        	# 'mobile':_dict.get('phone'),
        	'contact_name':_dict.get('Name'),
        	'email_from': _dict.get('Email'),
        }
        defaults.update(custom_values)
        return super(MyMailParser, self).message_new(msg_dict, custom_values=defaults)