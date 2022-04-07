from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    min_payment = fields.Float(
        string='Remuneración mínima vital',
        config_parameter='basic_rule.min_payment',
        default=0.0
    )
