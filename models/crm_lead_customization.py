from odoo import models, fields, api
@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class CrmLeadFields (models.Model):
    _inherit="crm.lead"

    client_lang= fields.Selection(_lang_get, string='Language', default=lambda self: self.env.lang,
                            help="If the selected language is loaded in the system, all documents related to "
                                 "this contact will be printed in this language. If not, it will be English.")    