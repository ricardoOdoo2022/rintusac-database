from datetime import datetime, time
from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    hr_allocation_ids = fields.Many2many(
        comodel_name='hr.leave.allocation',
        string='Asignaciones',
        compute='compute_hr_allocation_leave_ids'
    )
    leave_ids = fields.Many2many(
        comodel_name='hr.leave',
        string='Ausencias',
        compute='compute_hr_allocation_leave_ids'
    )

    @api.depends('date_from', 'date_to', 'contract_id')
    def compute_hr_allocation_leave_ids(self):
        for rec in self:
            allocations = []
            leaves = []
            if rec.date_from and rec.date_to and rec.contract_id and rec.contract_id.resource_calendar_id:
                day_from = datetime.combine(fields.Date.from_string(rec.date_from), time.min)
                day_to = datetime.combine(fields.Date.from_string(rec.date_to), time.max)
                calendar = rec.contract_id.resource_calendar_id
                day_leave_intervals = rec.contract_id.employee_id.list_leaves(day_from, day_to, calendar=calendar)
                for day, hours, leave in day_leave_intervals:
                    holiday = leave.holiday_id
                    if holiday:
                        leaves.append(holiday.id)
                        allocation = holiday.hr_leave_id
                        if allocation:
                            allocations.append(allocation.id)
            rec.hr_allocation_ids = list(set(allocations))
            rec.leave_ids = list(set(leaves))
