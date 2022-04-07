from odoo import api, fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    name = fields.Char(translate=True)
    max_percent = fields.Integer(string='Max.Salary Advance Percentage')
    advance_date = fields.Integer(string='Salary Advance-After days')


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    def _compute_employee_other_discounts(self):
        """This compute the other discount and total other discount count of an employee.
            """
        self.other_disc_count = self.env['hr.other.discounts'].search_count([('employee_id', '=', self.id)])

    other_disc_count = fields.Integer(string="Other Discounts Count", compute='_compute_employee_other_discounts')
    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    discount_line_ids = fields.Many2many('hr.other.discounts.line', string="Other Discounts Line")
    loan_line_ids = fields.Many2many('hr.loan.line', string="Loan Installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_inputs_data(self):
        res = super(HrPayslip, self).get_inputs_data()
        if not res:
            return res
        domain = [
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'approve'),
            ('contract_id', '=', self.contract_id.id)
        ]
        lon_obj = self.env['hr.loan'].search(domain)
        discount_obj = self.env['hr.other.discounts'].search(domain)

        loan_line_ids = []
        dsc_line_ids = []

        for loan in lon_obj:
            loan_line_ids += loan.loan_lines.filtered(lambda x: self.date_from <= x.date <= self.date_to and not x.paid and self.struct_id == x.struct_id)

        for dis in discount_obj:
            dsc_line_ids += dis.discount_lines.filtered(lambda x: self.date_from <= x.date <= self.date_to and not x.paid and self.struct_id == x.struct_id)

        adv_salary_ids = self.env['hr.salary.advance'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approve')])
        advance_amount = sum(adv_salary_ids.filtered(lambda x: x.date.month == self.date_from.month and x.date.year == self.date_from.year).mapped('advance'))
        for result in res:
            if result.get('code') == 'LO' and result.get('contract_id') == self.contract_id.id:
                result['amount'] = sum(loan_line.amount for loan_line in loan_line_ids) if loan_line_ids else 0
                result['loan_line_ids'] = [(6, 0, map(lambda x: x.id, loan_line_ids))] if loan_line_ids else False

            if result.get('code') == 'ODE_001' and result.get('contract_id') == self.contract_id.id:
                result['amount'] = sum(discount_line.amount for discount_line in dsc_line_ids) if dsc_line_ids else 0
                result['discount_line_ids'] = [(6, 0, map(lambda x: x.id, dsc_line_ids))] if dsc_line_ids else False

            if result.get('code') == 'SAR' and result.get('contract_id') == self.contract_id.id:
                result['amount'] = advance_amount
        return res

    def action_payslip_cancel(self):
        super(HrPayslip, self).action_payslip_cancel()
        for line in self.input_line_ids:
            if line.loan_line_ids:
                line.loan_line_ids.write({
                    'paid': False,
                    'payslip_id': False
                })
            if line.discount_line_ids:
                line.discount_line_ids.write({
                    'paid': False,
                    'payslip_id': False
                })

    def action_payslip_done(self):
        super(HrPayslip, self).action_payslip_done()
        for payslip in self:
            for line in payslip.input_line_ids:
                if line.loan_line_ids:
                    line.loan_line_ids.write({
                        'paid': True,
                        'payslip_id': payslip.id
                    })
                if line.discount_line_ids:
                    line.discount_line_ids.write({
                        'paid': True,
                        'payslip_id': payslip.id
                    })


class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    name = fields.Char(translate=True)


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    name = fields.Char(translate=True)
