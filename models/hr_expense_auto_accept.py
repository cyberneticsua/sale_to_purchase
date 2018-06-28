from odoo import models, fields, api
from odoo.exceptions import Warning
from odoo.exceptions import UserError

# class HrExpenseSheetAutoAccept (models.Model):
#     _inherit="hr.expense.sheet"

#     @api.model
#     def create(self, values):
#         sheet = super(
#             HrExpenseSheetAutoAccept, self).create(values)
#         if self.sudo().env.user.has_group(
#                 'hr_expense.group_hr_expense_user'):
#                 sheet.sudo().approve_expense_sheets()
#         return sheet

class HrExpenseAutoAccept(models.Model):
    
    _inherit = ['hr.expense']
    
    @api.multi
    def submit_expenses(self):
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report!"))
        # my_lines=self._move_line_get()
        # raise Warning(my_lines[0]['id'])
        # raise Warning(self.id)
        sheet = self.env['hr.expense.sheet'].create({
                # 'expense_line_ids': [line.id for line in self],
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