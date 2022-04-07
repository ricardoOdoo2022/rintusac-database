from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        string='Current Contract',
        help='Current contract of the employee',
        groups="hr.group_hr_user",
        domain="[('company_id', '=', company_id),('employee_id', '=', id)]"
    )
    service_start_date = fields.Date(
        string='Start Date',
        readonly=True,
        compute='compute_contract_date',
        store=True
    )
    service_termination_date = fields.Date(
        string='Termination Date',
        readonly=True,
        compute='compute_contract_date',
        store=True
    )

    @api.depends('contract_ids', 'contract_ids.date_start', 'contract_ids.date_end', 'contract_ids.state',
                 'contract_id')
    def compute_contract_date(self):
        for rec in self:
            if rec.contract_id:
                rec.service_start_date = rec.contract_id.date_start
                rec.service_termination_date = rec.contract_id.date_end
            else:
                contract = self.env['hr.contract']
                date_start = contract.search(rec._get_contract_filter(), order='date_start asc', limit=1)
                date_end = contract.search(rec._get_contract_filter(), order='date_end desc', limit=1)
                rec.service_start_date = date_start.date_start if date_start else False
                rec.service_termination_date = date_start.date_end if date_end else False

    @api.onchange('service_hire_date')
    def _onchange_service_hire_date(self):  # pragma: no cover
        # Do nothing
        pass

    def _get_contract_filter(self):
        self.ensure_one()

        return [('employee_id', '=', self.id), ('state', 'in', self._get_service_contract_states())]

    @api.model
    def _get_service_contract_states(self):
        return ['open', 'pending', 'close']

    @api.model
    def _action_update_service_duration(self):
        employees = self.search([])
        employees.compute_contract_date()
