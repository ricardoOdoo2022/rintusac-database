from lxml import etree
from collections import defaultdict
from odoo.exceptions import ValidationError
from odoo import models, fields, api
from odoo.addons.resource.models.resource import timezone_datetime
import logging

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    has_holidays = fields.Boolean(
        string='Vacaciones',
        groups="hr.group_hr_user"
    )
    holidays_per_year = fields.Char(
        string='Días de vacaciones por año',
        groups="hr.group_hr_user"
    )
    additional_days = fields.Char(
        string='Días adicionales',
        groups="hr.group_hr_user"
    )
    hr_allocation_ids = fields.One2many(
        comodel_name='hr.leave.allocation',
        inverse_name='employee_id',
        string='Líneas Vacaciones',
        groups="hr.group_hr_user"
    )

    def _get_work_days_data_batch_all(self, from_datetime, to_datetime, calendar=None):
        resources = self.mapped('resource_id')
        mapped_employees = {e.resource_id.id: e.id for e in self}
        result = {}

        # naive datetimes are made explicit in UTC
        from_datetime = timezone_datetime(from_datetime)
        to_datetime = timezone_datetime(to_datetime)

        mapped_resources = defaultdict(lambda: self.env['resource.resource'])
        for record in self:
            mapped_resources[calendar or record.resource_calendar_id] |= record.resource_id

        for calendar, calendar_resources in mapped_resources.items():
            day_total = calendar.with_context(holiday_status_id=True)._get_resources_day_total(from_datetime, to_datetime, calendar_resources)
            intervals = calendar.with_context(holiday_status_id=True)._attendance_intervals_batch(from_datetime, to_datetime, calendar_resources)

            for calendar_resource in calendar_resources:
                result[calendar_resource.id] = calendar._get_days_data(intervals[calendar_resource.id], day_total[calendar_resource.id])

        # convert "resource: result" into "employee: result"
        return {mapped_employees[r.id]: result[r.id] for r in resources}


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    to_date = fields.Date(
        string='Hasta'
    )
    from_date = fields.Date(
        string='Desde'
    )
    deadline = fields.Date(
        string='Tope de disfrute'
    )
    is_holiday = fields.Boolean(
        string='Es vacación?',
        compute='_compute_is_holiday',
        store=True
    )
    absence_ids = fields.One2many(
        comodel_name='hr.leave',
        inverse_name='hr_leave_id',
        string='Ausencias'
    )
    computed_holiday = fields.Float(
        string='Vacaciones computadas',
        compute='compute_days_holiday',
        store=True
    )
    used_holiday = fields.Float(
        string='Vac. gozadas o pagadas',
        compute='compute_days_holiday',
        store=True
    )
    pending_holiday = fields.Float(
        string='Vacaciones pendientes',
        compute='compute_days_holiday',
        store=True
    )

    @api.depends('number_of_days_display', 'absence_ids', 'absence_ids.number_of_days_display', 'absence_ids.state')
    def compute_days_holiday(self):
        for rec in self:
            rec.computed_holiday = rec.number_of_days_display or 0.0
            rec.used_holiday = sum(
                line.number_of_days_display for line in rec.absence_ids.filtered(lambda x: x.state == 'validate'))
            rec.pending_holiday = rec.computed_holiday - rec.used_holiday

    @api.depends('holiday_status_id')
    def _compute_is_holiday(self):
        holiday_id = self.env.ref('holiday_process.hr_leave_type_23', False)
        if holiday_id:
            for rec in self:
                if rec.holiday_status_id and rec.holiday_status_id == holiday_id:
                    rec.is_holiday = True

    def unlink(self):
        for rec in self:
            if rec.absence_ids:
                raise ValidationError('Primero debe eliminar las ausencias relacionadas.')
        return super(HrLeaveAllocation, self).unlink()

    def action_create_absence_holiday(self):
        holiday_id = self.env.ref('holiday_process.hr_leave_type_23')
        for rec in self:
            if rec.state == 'validate' or rec.state == 'validate1' and rec.holiday_status_id == holiday_id and \
                    rec.pending_holiday > 0:
                try:
                    self.env['hr.leave'].create({
                        'holiday_status_id': rec.holiday_status_id.id,
                        'employee_id': rec.employee_id.id,
                        'holiday_type': 'employee',
                        'hr_leave_id': rec.id
                    })
                except Exception as e:
                    _logger.warning(e)
                    continue


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    hr_leave_id = fields.Many2one(
        comodel_name='hr.leave.allocation',
        string='Asignación'
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HrLeave, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='hr_leave_id']"):
                leave_23_id = self.env.ref('holiday_process.hr_leave_type_23')
                leave_27_id = self.env.ref('automatic_leave_type.hr_leave_type_27')
                modifiers = f'{{"readonly": [["state", "not in", ["draft", "confirm"]]],' \
                            f' "invisible": [["holiday_status_id", "not in", [{leave_23_id.id}, {leave_27_id.id}]]]}}'
                node.set("modifiers", modifiers)
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.onchange('holiday_status_id')
    def onchange_holiday_status_id(self):
        leave_23_id = self.env.ref('holiday_process.hr_leave_type_23')
        leave_27_id = self.env.ref('automatic_leave_type.hr_leave_type_27')
        leave_ids = [leave_27_id.id, leave_23_id.id]
        if self.holiday_status_id and self.holiday_status_id.id in leave_ids:
            self.hr_leave_id = False


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        res = super(HrPayslip, self)._get_worked_day_lines(domain, check_out_of_contract)
        employee_id = self.contract_id.employee_id
        if self.contract_id.resource_calendar_id and employee_id.service_termination_date:
            leave_23 = self.env.ref('holiday_process.hr_leave_type_23')
            leaves = self.env['hr.leave'].search([
                ('holiday_status_id', '=', leave_23.id),
                ('employee_id', '=', employee_id.id),
                ('request_date_from', '<=', employee_id.service_termination_date),
                ('request_date_to', '>=', employee_id.service_termination_date),
                ('state', 'in', ['validate1', 'validate']),
            ])
            # VAC_LBS
            vac_lbs_days = sum(line.number_of_days_display for line in leaves)
            hours_per_day = self.contract_id.resource_calendar_id.hours_per_day or 0.0
            vac_lbs_hours = vac_lbs_days * hours_per_day
            vac_lbs_entry_type_id = self.env.ref('holiday_process.hr_work_entry_type_vac_lbs')

            values = [{
                'sequence': vac_lbs_entry_type_id.sequence, 'work_entry_type_id': vac_lbs_entry_type_id.id, 'number_of_days': vac_lbs_days,
                'number_of_hours': vac_lbs_hours
            }]
            res += values
        return res
