from odoo import api, fields, models


class ComisSystemPension(models.Model):
    _name = 'comis.system.pension'
    _description = 'Comisión Sistema de Pensión'

    date_from = fields.Date(
        string='Desde',
        required=True
    )
    date_to = fields.Date(
        string='Hasta',
        required=True
    )
    fund = fields.Float(string='Fondo')
    bonus = fields.Float(string='Prima')
    mixed_flow = fields.Float(string='Flujo / Mixta')
    flow = fields.Float(string='Flujo')
    balance = fields.Float(string='Saldo')
    pension_id = fields.Many2one(
        comodel_name='pension.system',
        string='Sistema de pension'
    )
