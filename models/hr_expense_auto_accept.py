from odoo import models, fields, api
from odoo.exceptions import Warning
from odoo.exceptions import UserError

class HrExpenseAutoAccept(models.Model):
    
    _inherit = ['hr.expense']
    
    @api.multi
    def submit_expenses(self):
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report!"))
        sheet = self.env['hr.expense.sheet'].create({
                'employee_id': self[0].employee_id.id,
                'name': self[0].name if len(self.ids) == 1 else '',
                'state':'approve',
                'responsible_id': self.env.user.id
                })
        self.sheet_id=sheet.id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'res_id':sheet.id,
            'target': 'current',
        }