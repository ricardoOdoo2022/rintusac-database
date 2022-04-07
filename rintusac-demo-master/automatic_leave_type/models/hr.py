from odoo import api, fields, models


class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    is_calc_own_rule = fields.Boolean(string='¿Es calculado por su propia regla?')

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    code = fields.Char(string='Código')
    validity_start = fields.Date(string='Validity Start')
    validity_stop = fields.Date(string='Validity Stop')