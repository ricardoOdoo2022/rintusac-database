from odoo import api, fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    plame_ids = fields.Many2many(
        comodel_name='plame.lines',
        string='Código Plame'
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    code_file_plame = fields.Char(
        string='Código archivo Plame',
        config_parameter='process_plame.code_file_plame',
    )
