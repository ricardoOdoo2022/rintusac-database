from odoo import models, fields, api


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    exception_ids = fields.Many2many(
        comodel_name='payroll.projection.exception',
        string='Renta de 5ta.',
        domain=[('is_active', '=', True)]
    )
