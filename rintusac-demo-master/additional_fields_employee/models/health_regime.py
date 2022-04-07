from odoo import models, fields


class HealthRegime(models.Model):
    _name = 'health.regime'
    _description = 'Régimen de Salud'

    code = fields.Char(string='Código')
    health_description = fields.Char(string='Descripción')
    name = fields.Char(string='Abreviatura')
