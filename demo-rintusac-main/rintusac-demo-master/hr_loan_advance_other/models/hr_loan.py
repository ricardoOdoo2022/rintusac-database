from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            self.total_amount = loan.loan_amount
            self.balance_amount = balance_amount
            self.total_paid_amount = total_paid

    name = fields.Char(string="Loan Name", default="/", readonly=True)
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department")
    installment = fields.Integer(string="No Of Installments", default=1, required=True)
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today())
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    emp_account_id = fields.Many2one('account.account', string="Loan Account")
    treasury_account_id = fields.Many2one('account.account', string="Treasury Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    loan_amount = fields.Float(string="Loan Amount", required=True)
    total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_loan_amount')
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_loan_amount')
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_loan_amount')
    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('waiting_approval_2', 'Waiting Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', copy=False, )
    loan_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], string="Loan type", default='daily', required=True)

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    @api.onchange('employee_id')
    def _onchange_contract_id(self):
        if self.employee_id and self.date:
            contract_ids = self.get_contract(self.employee_id, self.date, self.date)
            if contract_ids:
                self.contract_id = contract_ids[0]
        domain = [('employee_id', '=', self.employee_id.id)]
        return {'domain': {'contract_id': domain}}

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
        res = super(HrLoan, self).create(values)
        return res

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        for rec in self:
            if not rec.contract_id:
                raise ValidationError("Contract's field should not be empty.")
            rec.write({'state': 'waiting_approval_1'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.write({'state': 'approve'})

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()

    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment

            contracts = loan.employee_id._get_contracts(loan.payment_date, loan.payment_date)
            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                struct_id = False
            else:
                struct_id = contracts[0].structure_type_id.default_struct_id.id

            if loan.loan_type == 'daily':
                relative_values = relativedelta(days=1)
            elif loan.loan_type == 'weekly':
                relative_values = relativedelta(days=7)
            elif loan.loan_type == 'monthly':
                relative_values = relativedelta(months=1)
            elif loan.loan_type == 'quarterly':
                relative_values = relativedelta(months=3)
            else:
                relative_values = relativedelta(years=1)
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'struct_id': struct_id,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id
                })
                date_start = date_start + relative_values
        return True


class HrLoanLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True)
    amount = fields.Float(string="Amount", required=True)
    paid = fields.Boolean(string="Paid")
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Employee"
    )
    loan_id = fields.Many2one(
        comodel_name='hr.loan',
        string="Loan Ref."
    )
    payslip_id = fields.Many2one(
        comodel_name='hr.payslip',
        string="Payslip Ref."
    )
    struct_id = fields.Many2one(
        comodel_name='hr.payroll.structure',
        string='Salary Structure'
    )

    @api.model
    def default_get(self, field_list):
        result = super(HrLoanLine, self).default_get(field_list)
        if result.get('employee_id', False):
            employee = self.env['hr.employee'].browse(result['employee_id'])
            today = fields.Date.today()
            contracts = employee._get_contracts(today, today)
            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                result['struct_id'] = False
            result['struct_id'] = contracts[0].structure_type_id.default_struct_id.id
        return result
