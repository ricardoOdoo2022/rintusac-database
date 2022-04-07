from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
import logging
import math
import pytz

logger = logging.getLogger(__name__)
days = ([
    ('0', 'LUNES'),
    ('1', 'MARTES'),
    ('2', 'MIÉRCOLES'),
    ('3', 'JUEVES'),
    ('4', 'VIERNES'),
    ('5', 'SÁBADO'),
    ('6', 'DOMINGO')
])


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    hr_attendance_ids = fields.One2many(
        comodel_name='hr.attendance',
        inverse_name='leave_id',
        string='Asistencias'
    )
    report_attendance = fields.Boolean(
        string='¿Reportar en asistencia?',
        default=True
    )

    @staticmethod
    def get_period_odd_even_week():
        # 1 == odd week    || 0 == even week
        today = fields.Date.today()
        week_type = '1' if int(math.floor((today.toordinal() - 1) / 7) % 2) else '0'
        return week_type

    @api.model
    def _action_absence_monitor(self):
        employees = self.env['hr.employee'].search([
            ('active', '=', True),
            ('attendance', '=', True)
        ])
        today = self._convert_date_timezone(datetime.now())
        today_date = str(today)[:10]

        date_order_start = self._convert_date_timezone_to_utc('{} 00:00:00'.format(today_date))
        date_order_end = self._convert_date_timezone_to_utc('{} 23:59:59'.format(today_date))

        for employee in employees:
            attendance = self.env['hr.attendance'].search([
                ('check_in', '>=', date_order_start),
                ('check_in', '<=', date_order_end),
                ('employee_id', '=', employee.id)
            ])

            if not attendance:
                str_name = today_date
                schedule = employee.resource_calendar_id
                index = str(today.weekday())
                if schedule.two_weeks_calendar:
                    week_type = self.get_period_odd_even_week()
                    line_schedule = sorted(schedule.attendance_ids.filtered(
                        lambda x: x.dayofweek == index and x.day_period == 'morning' and
                                  x.week_type == week_type and x.display_type != 'line_section'), key=lambda x: x.hour_from)
                else:
                    line_schedule = sorted(schedule.attendance_ids.filtered(
                        lambda x: x.dayofweek == index and x.day_period == 'morning'), key=lambda x: x.hour_from)
                if not line_schedule:
                    continue
                elif len(line_schedule) > 1:
                    values = self.get_hr_leave_values(line_schedule[0], line_schedule[1], str_name, employee)
                    if self.validate_global_off_and_day_off(line_schedule[0], values) or self.validate_global_off_and_day_off(line_schedule[1], values):
                        continue
                else:
                    values = self.get_hr_leave_values(line_schedule[0], line_schedule[0], str_name, employee)
                    if self.validate_global_off_and_day_off(line_schedule[0], values):
                        continue
                try:
                    hr_leave = self.env['hr.leave'].create(values)
                    self._cr.commit()
                except Exception as error:
                    logger.error("Ausencia no creada: \n -Empleado: {}\n -Error: {}".format(employee.name, error))
                    self._cr.rollback()
                    continue
                logger.info("Ausencia creada: \n -Empleado: {}".format(employee.name))
                attendance_id = self.env['hr.attendance'].create({
                    'employee_id': employee.id,
                    'check_in': hr_leave.date_from,
                    'check_out': hr_leave.date_to,
                    'holiday_status_id': hr_leave.holiday_status_id.id,
                    'leave_id': hr_leave.id
                })

    def validate_global_off_and_day_off(self, resource_attendance_id, attendance_data):
        date_from = attendance_data['date_from']
        date_to = attendance_data['date_to']
        flag = False
        if resource_attendance_id.work_entry_type_id and resource_attendance_id.work_entry_type_id == self.env.ref('absence_day.hr_work_entry_type_ddo'):
            flag = True
        calendar_id = resource_attendance_id.calendar_id
        if calendar_id.global_leave_ids and calendar_id.global_leave_ids.filtered(lambda x: x.date_from <= date_from and x.date_to >= date_to):
            flag = True
        return flag

    def get_hr_leave_values(self, line_morning, line_afternoon, str_name, employee):
        hr_leave_type_id = self.env.ref('absence_manager.hr_leave_type_ppd', False)
        hour = str(line_morning[0].hour_from).replace('.', ':')
        date_order_start = self._convert_date_timezone_to_utc('{} {}:00'.format(str_name, hour))
        hour = str(line_afternoon[0].hour_to).replace('.', ':')
        date_order_end = self._convert_date_timezone_to_utc('{} {}:00'.format(str_name, hour))
        values = {
            'employee_id': employee.id,
            'holiday_status_id': hr_leave_type_id.id,
            'request_date_from': date_order_start,
            'request_date_to': date_order_end,
            'date_from': date_order_start,
            'date_to': date_order_end,
            'state': 'confirm',
            'holiday_type': 'employee',
            'number_of_days': '1',
            'report_attendance': False
        }
        return values

    def _convert_date_timezone_to_utc(self, date_order, format_time='%Y-%m-%d %H:%M:%S'):
        tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
        date_order = datetime.strptime(date_order, format_time)
        datetime_with_tz = tz.localize(date_order, is_dst=None)
        date_order = datetime_with_tz.astimezone(pytz.utc).replace(tzinfo=None)
        return date_order

    def _convert_date_timezone(self, date_order, format_time='%Y-%m-%d %H:%M:%S'):
        tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
        if isinstance(date_order, str):
            date_order = datetime.strptime(date_order, format_time)
        if date_order:
            date_tz = pytz.utc.localize(date_order).astimezone(tz)
            date_order = date_tz.strftime(format_time)
            date_order = datetime.strptime(date_order, format_time)
        return date_order

    def write(self, vals):
        ret = super(HrLeave, self).write(vals)
        if vals.get('holiday_status_id') and self.hr_attendance_ids:
            for attendance in self.hr_attendance_ids:
                attendance.holiday_status_id = vals['holiday_status_id']
        return ret

    def create_attendance_period(self, request_date_from, request_date_to, employee_id, leave):
        attendance_list = []
        holiday_status_id = leave.holiday_status_id
        while request_date_from <= request_date_to:
            try:
                check_out = '{}{}'.format(str(request_date_from)[:10], str(request_date_to)[10:])
                attendance = self.env['hr.attendance'].create({
                    'employee_id': employee_id.id,
                    'check_in': request_date_from,
                    'check_out': check_out,
                    'holiday_status_id': holiday_status_id.id
                })
                request_date_from += relativedelta(days=1)
                attendance_list.append(attendance.id)
            except Exception:
                request_date_from += relativedelta(days=1)
        return attendance_list

    def action_approve(self):
        super(HrLeave, self).action_approve()
        for rec in self:
            if not rec.hr_attendance_ids and rec.report_attendance:
                hr_attendance_ids = rec.create_attendance_period(rec.date_from, rec.date_to, rec.employee_id, rec)
                rec.hr_attendance_ids = [(6, 0, hr_attendance_ids)]

    def action_refuse(self):
        super(HrLeave, self).action_refuse()
        for rec in self:
            if rec.report_attendance:
                rec.hr_attendance_ids.unlink()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance = fields.Boolean(
        string='¿Está obligado a marcar asistencia?',
        groups="hr.group_hr_user",
        default=True
    )

    @api.depends('attendance_ids')
    def _compute_last_attendance_id(self):
        for employee in self:
            record = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False),
            ], limit=1)
            if not record:
                record = self.env['hr.attendance'].search([('employee_id', '=', employee.id)], limit=1)
            employee.last_attendance_id = record


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    leave_id = fields.Many2one(
        comodel_name='hr.leave',
        string='Ausencia'
    )
    holiday_status_id = fields.Many2one(
        comodel_name="hr.leave.type",
        string="Tipo de Ausencia",
        readonly=True
    )

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    code = fields.Char(string='Código')