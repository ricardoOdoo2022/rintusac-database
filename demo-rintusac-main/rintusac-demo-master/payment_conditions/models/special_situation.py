from odoo import api, fields, models


class SpecialSituation(models.Model):
    _name = 'special.situation'
    _description = 'Situación especial'

    code = fields.Char(string='Código')
    situation_description = fields.Char(string='Descripción')
    name = fields.Char(string='Abreviatura')
