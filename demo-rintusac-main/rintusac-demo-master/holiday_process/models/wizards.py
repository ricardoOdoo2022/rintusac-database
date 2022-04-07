from asyncio.log import logger
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import pytz

_logger = logging.getLogger(__name__)


def _convert_date_timezone_to_utc(user, date_order, format_time='%Y-%m-%d %H:%M:%S'):
    tz = pytz.timezone(user.tz) if user.tz else pytz.utc
    date_order = datetime.strptime(date_order, format_time)
    datetime_with_tz = tz.localize(date_order, is_dst=None)
    date_order = datetime_with_tz.astimezone(pytz.utc)
    date_order = datetime.strftime(date_order, format_time)
    return date_order


class HolidaysGeneratorWizard(models.TransientModel):
    _name = 'holiday.generator.wizard'
    _description = 'Generador de vacaciones'

    employees_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Empleados'
    )
    is_generated = fields.Boolean(
        string='Fue generado?'
    )
    set_period = fields.Boolean(
        string='Definir periodo'
    )
    date_from = fields.Date(
        string='Desde',
    )
    date_to = fields.Date(
        string='Hasta',
    )

    @api.onchange('set_period')
    def onchange_set_period(self):
        self.date_from = self.date_to = False

    def action_generate_holidays(self):
        if self.employees_ids:
            employees = self.employees_ids
        else:
            employees = self.env['hr.employee'].search([
                ('has_holidays', '=', True),
                ('service_start_date', '!=', False)
            ])
        arr_employee = []
        for employee in employees:
            start_date = employee.service_start_date
            end_tdate = employee.service_termination_date
            arr_employee = self.set_period_holidays(
                employee, start_date, end_tdate, arr_employee)
        arr_employee = list(set(arr_employee))
        form = self.env.ref(
            'holiday_process.holiday_generator_wizard_view_form')
        return {
            'name': 'Empleados con vacaciones generadas',
            'res_model': self._name,
            'view_mode': 'form',
            'views': [(form.id, 'form')],
            'context': {'default_is_generated': True, 'default_employees_ids': arr_employee},
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def set_period_holidays(self, employee, start_date, end_tdate, arr_employee):
        today = fields.Date.today()
        end_date = start_date + relativedelta(months=12)
        start_date, end_date, arr_employee = self.generate_holidays(
            start_date, end_date, employee, arr_employee)
        if end_tdate:
            while start_date.year <= end_tdate.year:
                start_date, end_date, arr_employee = self.generate_holidays(
                    start_date, end_date, employee, arr_employee)
        else:
            while end_date.year <= today.year or start_date.year <= today.year <= end_date.year:
                start_date, end_date, arr_employee = self.generate_holidays(
                    start_date, end_date, employee, arr_employee)
        return arr_employee

    def generate_holidays(self, start_date, end_date, employee, arr_employee):
        years = [] if not self.set_period else list(
            range(self.date_from.year, self.date_to.year + 1))
        if start_date.year in years or not self.set_period:
            holiday_id = self.env.ref('holiday_process.hr_leave_type_23')
            rec = self.env['hr.leave.allocation'].search([
                ('from_date', '=', start_date),
                ('to_date', '=', end_date),
                ('holiday_status_id', '=', holiday_id.id),
                ('employee_id', '=', employee.id)
            ])
            if not rec:
                date_order_from = _convert_date_timezone_to_utc(
                    self.env.user, '{} 00:00:00'.format(start_date))
                date_order_to = _convert_date_timezone_to_utc(
                    self.env.user, '{} 00:00:00'.format(end_date))
                nro_days = int(employee.additional_days) + \
                    int(employee.holidays_per_year)
                allocation_id = self.env['hr.leave.allocation'].create({
                    'name': 'Vacaciones {} {}'.format(start_date, end_date),
                    'holiday_status_id': holiday_id.id,
                    'to_date': end_date,
                    'from_date': start_date,
                    'allocation_type': 'accrual',
                    'date_from': date_order_from,
                    'date_to': date_order_to,
                    'holiday_type': 'employee',
                    'employee_id': employee.id,
                    'number_of_days': 0,
                    'unit_per_interval': 'days',
                    'number_per_interval': nro_days / 12,
                    'interval_number': 1,
                    'interval_unit': 'months',
                    'deadline': end_date + relativedelta(months=8),
                })
                try:
                    allocation_id.action_approve()
                    allocation_id._update_accrual_allocation()
                except Exception as e:
                    _logger.info('Vacación no aprobada:\n  .Empleado: {}\n  .Asignación:{}\n  .Error:{}'.format(
                        employee.name, allocation_id.id, e))
                arr_employee.append(employee.id)
        start_date += relativedelta(months=12)
        end_date = start_date + relativedelta(months=12)
        return start_date, end_date, arr_employee


class HolidayPetitionWizard(models.TransientModel):
    _name = 'holiday.petition.wizard'
    _description = 'Solicitud y compensación de vacaciones'

    nro_holidays = fields.Float(
        string='N° de días de Vacaciones',
        required=True
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Empleado',
        required=True
    )
    from_date = fields.Date(
        string='Desde',
        required=True
    )
    to_date = fields.Date(
        string='Hasta',
        compute='_compute_to_date',
        store=True
    )
    holiday_status_id = fields.Many2one(
        comodel_name='hr.leave.type',
        string='Tipo de Ausencia',
        required=True,
        default=lambda self: self.env.ref('holiday_process.hr_leave_type_23')
    )
    is_generated = fields.Boolean(
        string='Fue generado?'
    )
    allocation_ids = fields.Many2many(
        comodel_name='hr.leave.allocation',
        string='Asignaciones',
        compute='_compute_allocation_ids',

    )
    msj = fields.Char(
        string='Mensaje',
        readonly=True
    )
    absence_ids = fields.Many2many(
        comodel_name='hr.leave',
        string='Ausencias'
    )
    is_settlement = fields.Boolean(
        string='¿Es liquidación?'
    )

    @api.depends('employee_id', 'holiday_status_id')
    def _compute_allocation_ids(self):
        for rec in self:
            if rec.employee_id and rec.holiday_status_id:
                allocation_ids = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('holiday_status_id', '=', rec.holiday_status_id.id),
                    ('pending_holiday', '>', 0)
                ])
                rec.allocation_ids = allocation_ids
            else:
                rec.allocation_ids = False

    @api.depends('nro_holidays', 'from_date')
    def _compute_to_date(self):
        for rec in self:
            if rec.nro_holidays and rec.from_date:
                rec.to_date = rec.from_date + \
                    relativedelta(days=rec.nro_holidays)

    @api.constrains('from_date', 'to_date')
    def _check_dates(self):
        for rec in self:
            if rec.from_date and rec.to_date:
                if rec.from_date > rec.to_date:
                    raise ValidationError(
                        'La fecha "Desde" no puede ser mayor que la fecha "Hasta".')

    def action_generate_holidays(self):
        if self.nro_holidays <= 0:
            raise ValidationError(
                'El número de días de vacaciones no pueden ser menor o igual a 0.')
        hr_allocation_ids = self.allocation_ids
        logger.info('hr_allocation_ids: {}'.format(hr_allocation_ids))
        nro = self.nro_holidays
        logger.info('nro: {}'.format(nro))
        total_pending_holiday = sum(
            line.pending_holiday for line in hr_allocation_ids)
        for line in hr_allocation_ids:
            logger.info('line.pending_holiday: {}'.format(line.pending_holiday))    
        logger.info('total_pending_holiday: {}'.format(total_pending_holiday))
        context = {
            'default_is_generated': True,
            'default_employee_id': self.employee_id.id,
            'default_from_date': self.from_date,
            'default_to_date': self.to_date,
            'default_holiday_status_id': self.holiday_status_id.id,
        }

        if total_pending_holiday < nro:
            context.update({
                'default_msj': 'La sumatoria total de días pendientes de las asignaciones "{}"'
                               ' es menor que la cantidad de días a asignar "{}".'.format(
                                   total_pending_holiday, nro)
            })
        else:
            absences = []
            request_date_from = self.from_date
            for allocation in hr_allocation_ids.sorted(key=lambda r: r.from_date):
                if nro > 0:
                    days = allocation.pending_holiday if nro >= allocation.pending_holiday else nro
                    absence_id = self.create_holiday_absences(
                        request_date_from, days, allocation)
                    absences.append(absence_id.id)
                    if not self._context.get('settlement'):
                        request_date_from += relativedelta(days=days)
                    nro -= days
                    if nro <= 0 and self._context.get('settlement'):
                        allocation.date_to = absence_id.date_to
                        break

            context.update({
                'default_absence_ids': absences,
            })
        return self.action_reopen_wizard(context=context)

    def action_reopen_wizard(self, context=None):
        if self._context.get('settlement'):
            form = self.env.ref(
                'holiday_process.holiday_settlement_wizard_view_form')
            name = 'Compensación de vacaciones'
        else:
            form = self.env.ref(
                'holiday_process.holiday_petition_wizard_view_form')
            name = 'Solicitud de vacaciones'
        if context:
            if context.get('active_id'):
                if context.get('default_absence_ids'):
                    del context['default_absence_ids']
                if context.get('default_allocation_ids'):
                    del context['default_allocation_ids']
                del context['active_id']
                del context['active_ids']
                del context['default_is_generated']
        return {
            'name': name,
            'res_model': self._name,
            'view_mode': 'form',
            'views': [(form.id, 'form')],
            'context': context,
            'view_id': form.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def create_holiday_absences(self, from_date, total_days, allocation_id):
        if self._context.get('settlement'):
            to_date = from_date
        else:
            to_date = from_date + relativedelta(days=total_days)
        absence_id = self.env['hr.leave'].create({
            'holiday_status_id': self.holiday_status_id.id,
            'employee_id': self.employee_id.id,
            'holiday_type': 'employee',
            'hr_leave_id': allocation_id.id, 'request_date_to': to_date,
            'request_date_from': from_date,

            # minutes are not zero because when it's the same date _onchange_leave_dates do not calc one day
            'date_from': _convert_date_timezone_to_utc(self.env.user, '{} 08:00:00'.format(from_date)),
            'date_to': _convert_date_timezone_to_utc(self.env.user, '{} 17:00:00'.format(to_date))
        })
        #absence_id._onchange_leave_dates()
        if self._context.get('settlement'):
            absence_id.name = """Esta ausencia no ha sido gozada, sino que se ha creado para dejar constancia 
            que ya se han pagado por medio de una compra o liquidación."""
            query = """UPDATE hr_leave set number_of_days = {} where id = {}""".format(
                total_days, absence_id.id)
            self._cr.execute(query)
        return absence_id
