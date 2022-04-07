from odoo import api, fields, models


class VariablePayment(models.Model):
    _name = 'variable.payment'
    _description = 'Pago Variable'

    code = fields.Char(string='Código')
    name = fields.Char(string='Descripción')
