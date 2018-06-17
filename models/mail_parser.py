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
        fields=['Name:','Phone:','UTM source','UTM medium','UTM campaign']
        _dict={}
		# description=description.lower()
        for field in fields:
            index = s.find(field)
            if (index>0):
                last_index=s.find("<",index)
                _dict[field]=s[index+len(field):last_index]
        index = s.find('Email:')
        index=s.find("mailto:",index)
        if (index>0):
            last_index=s.find("\"",index)
            _dict['Email']=s[index+len("mailto:"):last_index]

        if 'UTM campaign' in _dict:
            record=self.env['utm_campaign'].search([('name','=',_dict['UTM campaign'])])
            if not(record):
                record=self.env['utm_campaign'].create({'name':_dict['UTM campaign']})
            defaults['campaign_id']=record.id
        
        if 'UTM medium' in _dict:
            record=self.env['utm_medium'].search([('name','=',_dict['UTM medium'])])
            if not(record):
                record=self.env['utm_medium'].create({'name':_dict['UTM medium']})
            defaults['medium_id']=record.id

        if 'UTM source' in _dict:
            record=self.env['utm_source'].search([('name','=',_dict['UTM source'])])
            if not(record):
                record=self.env['utm_source'].create({'name':_dict['UTM source']})
            defaults['source_id']=record.id

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