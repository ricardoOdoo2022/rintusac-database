import time
import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, Warning

_logger = logging.getLogger(__name__)


class HrSalaryAdvance(models.Model):
    _name = "hr.salary.advance"
    _description = 'Salary Advance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', readonly=True, default=lambda self: 'Adv/')
    reason = fields.Text(string='Reason')
    date = fields.Date(string='Date', required=True, default=lambda self: fields.Date.today())
    advance = fields.Float(string='Advance', required=True)
    exceed_condition = fields.Boolean(string='Exceed than maximum', help="The Advance is greater than the maximum percentage in salary structure")
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submitted'),
                              ('waiting_approval', 'Waiting Approval'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('reject', 'Rejected')], string='Status', default='draft')
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency'
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id
    )
    payment_method = fields.Many2one(
        comodel_name='account.journal',
        string='Payment Method'
    )
    department = fields.Many2one(
        comodel_name='hr.department',
        string='Department'
    )
    debit = fields.Many2one(
        comodel_name='account.account',
        string='Debit Account'
    )
    credit = fields.Many2one(
        comodel_name='account.account',
        string='Credit Account'
    )
    journal = fields.Many2one(
        comodel_name='account.journal',
        string='Journal'
    )
    employee_contract_id = fields.Many2one(
        comodel_name='hr.contract',
        string='Contract'
    )

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        department_id = self.employee_id.department_id.id
        contract_id = self.get_contract(self.employee_id, self.date, self.date)
        domain = [('employee_id', '=', self.employee_id.id)]
        return {
            'value': {
                'department': department_id,
                'employee_contract_id': contract_id
            },
            'domain': {'employee_contract_id': domain}
        }

    @api.model
    def get_contract(self, employee, date_from, date_to):
        if not employee:
            return False
        if not date_to:
            date_to = date_from
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        contract = self.env['hr.contract'].search(clause_final, limit=1)
        return contract.id if contract else False

    @api.onchange('company_id')
    def onchange_company_id(self):
        company = self.company_id
        domain = [('company_id.id', '=', company.id)]
        result = {'domain': {'journal': domain}}
        return result

    def back_to_draft(self):
        self.ensure_one()
        self.state = 'draft'

    def submit_to_manager(self):
        self.ensure_one()
        self.state = 'submit'

    def cancel(self):
        self.ensure_one()
        self.state = 'cancel'

    def reject(self):
        self.ensure_one()
        self.state = 'reject'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('hr.salary.advance.seq') or ' '
        res_id = super(HrSalaryAdvance, self).create(vals)
        return res_id

    def approve_request(self):
        """This Approve the employee salary advance request. """
        self.ensure_one()
        emp_obj = self.env['hr.employee']
        address = emp_obj.browse([self.employee_id.id]).address_home_id
        if not address.id:
            raise AccessError('Define home address for employee')

        current_month = datetime.strptime(str(self.date), '%Y-%m-%d').date().month

        if not self.employee_contract_id:
            raise AccessError('Define a contract for the employee')
        struct_id = self.employee_contract_id.struct_id
        if not struct_id.max_percent or not struct_id.advance_date:
            raise AccessError('Max percentage or advance days are not provided in Contract')
        adv = self.advance
        amt = (self.employee_contract_id.struct_id.max_percent * self.employee_contract_id.wage) / 100
        if adv > amt and not self.exceed_condition:
            raise AccessError('Advance amount is greater than allotted')

        if not self.advance:
            raise AccessError('You must Enter the Salary Advance amount')
        payslip_obj = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id),
                                                     ('state', '=', 'done'), ('date_from', '<=', self.date),
                                                     ('date_to', '>=', self.date)])
        if payslip_obj:
            raise AccessError('This month salary already calculated.')

        for slip in self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)]):
            slip_moth = datetime.strptime(str(slip.date_from), '%Y-%m-%d').date().month
            if current_month == slip_moth + 1:
                slip_day = datetime.strptime(str(slip.date_from), '%Y-%m-%d').date().day
                current_day = datetime.strptime(str(self.date), '%Y-%m-%d').date().day
                if current_day - slip_day < struct_id.advance_date:
                    raise Warning(_('Request can be done after "%s" Days From previous month salary') % struct_id.advance_date)
        self.state = 'waiting_approval'

    def approve_request_acc_dept(self):
        """This Approve the employee salary advance request from accounting department.
                   """
        self.ensure_one()
        if not self.debit or not self.credit or not self.journal:
            raise AccessError("You must enter Debit & Credit account and journal to approve.")
        if not self.advance:
            raise AccessError("You must Enter the Salary Advance amount.")

        move_obj = self.env['account.move'].with_context(default_type='entry')
        timenow = time.strftime('%Y-%m-%d')
        line_ids = []
        debit_sum = 0.0
        credit_sum = 0.0
        for request in self:
            amount = request.advance
            request_name = request.employee_id.name
            reference = request.name
            journal_id = request.journal.id
            move = {
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow
            }

            debit_account_id = request.debit.id
            credit_account_id = request.credit.id

            if debit_account_id:
                debit_line = (0, 0, {
                    'name': request_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'currency_id': self.currency_id and self.currency_id.id,
                })
                line_ids.append(debit_line)
                debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

            if credit_account_id:
                credit_line = (0, 0, {
                    'name': request_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'currency_id': self.currency_id and self.currency_id.id,
                })
                line_ids.append(credit_line)
                credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            move.update({'line_ids': line_ids})
            move_obj.create(move)
            try:
                move_obj.action_post()
            except Exception:
                _logger.debug('Error publishing move: {}'.format(move_obj))
            self.state = 'approve'
            return True
