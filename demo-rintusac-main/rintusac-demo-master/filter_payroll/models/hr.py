from odoo import api, fields, models


class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    unpaid = fields.Boolean(string='Es no Pagada?')
    is_social_benefits_license = fields.Boolean(string='¿Es Licencia para Benef. Sociales?')
    is_benefits_license_absence = fields.Boolean(string='¿Es Inasistencia para Benef. Sociales?')


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    
    unpaid = fields.Boolean(related='work_entry_type_id.unpaid')
    is_social_benefits_license = fields.Boolean(
        string='¿Es Licencia para Benef. Sociales?',
        related='work_entry_type_id.is_social_benefits_license'
    )
    is_benefits_license_absence = fields.Boolean(
        string='¿Es Inasistencia para Benef. Sociales?',
        related='work_entry_type_id.is_benefits_license_absence'
    )
    is_calc_own_rule = fields.Boolean(
        string='¿Es calculado por su propia regla?',
        related='work_entry_type_id.is_calc_own_rule'
    )


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    unpaid = fields.Boolean(
        string='Es no Pagada?',
        related='work_entry_type_id.unpaid'
    )
    is_social_benefits_license = fields.Boolean(
        string='¿Es licencia para Benef. Sociales?',
        related='work_entry_type_id.is_social_benefits_license'
    )
    is_benefits_license_absence = fields.Boolean(
        string='¿Es inasistencia para Benef. Sociales?',
        related='work_entry_type_id.is_benefits_license_absence'
    )
    is_calc_own_rule = fields.Boolean(
        string='¿Es calculado por su propia regla?',
        related='work_entry_type_id.is_calc_own_rule'
    )


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    unpaid = fields.Boolean(
        string='Is Unpaid',
        related='holiday_status_id.unpaid'
    )
    is_social_benefits_license = fields.Boolean(
        string='¿Es Licencia para Benef. Sociales?',
        related='holiday_status_id.is_social_benefits_license'
    )
    is_benefits_license_absence = fields.Boolean(
        string='¿Es Inasistencia para Benef. Sociales?',
        related='holiday_status_id.is_benefits_license_absence'
    )
    is_calc_own_rule = fields.Boolean(
        string='¿Es calculado por su propia regla?',
        related='holiday_status_id.is_calc_own_rule'
    )
    code_holiday = fields.Char(
        string='Código ausencia',
        related='holiday_status_id.code'
    )


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    is_social_benefits_license = fields.Boolean(
        string='¿Es Licencia para Benef. Sociales?',
        related='holiday_status_id.is_social_benefits_license'
    )
    is_benefits_license_absence = fields.Boolean(
        string='¿Es Inasistencia para Benef. Sociales?',
        related='holiday_status_id.is_benefits_license_absence'
    )
    is_calc_own_rule = fields.Boolean(
        string='¿Es calculado por su propia regla?',
        related='holiday_status_id.is_calc_own_rule'
    )
    unpaid = fields.Boolean(
        string='Is Unpaid',
        related='holiday_status_id.unpaid'
    )
    code_holiday = fields.Char(
        string='Código ausencia',
        related='holiday_status_id.code'
    )
