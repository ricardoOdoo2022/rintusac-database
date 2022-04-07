from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_sheet(self):
        for payslip in self.filtered(lambda slip: slip.state not in ['cancel', 'done']):
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            lines = [(0, 0, line) for line in payslip._get_payslip_lines() if line['amount'] != 0]
            payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
        return True

    def action_payslip_done(self):
        super(HrPayslip, self).action_payslip_done()
        for rec in self:
            days_lines = rec.worked_days_line_ids.filtered(lambda x: x.number_of_days == 0)
            days_lines.unlink()
            input_lines = rec.input_line_ids.filtered(lambda x: x.amount == 0)
            input_lines.unlink()

    # TODO
    """
    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        super(HrPayslip, self)._onchange_employee()
        self.get_inputs()
    """
    
    
    def get_inputs_data(self):
        input_values = []
        input_ids = self.struct_id.input_line_type_ids
        for input_line in input_ids:
            input_data = {
                'input_type_id': input_line.id,
                'code': input_line.code,
                'contract_id': self.contract_id.id,
            }
            input_values.append(input_data)
        return input_values

    def get_inputs(self):
        self.ensure_one()
        input_values = self.get_inputs_data()
        input_lines = self.input_line_ids.browse([])
        for values in input_values:
            input_lines |= input_lines.new(values)
        self.input_line_ids = input_lines
