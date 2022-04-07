from odoo import api, fields, models


class PaymentType(models.Model):
    _name = 'payment.type'
    _description = 'Tipo de Pago'

    code = fields.Char(string='Código')
    payment_description = fields.Char(string='Descripción')
    name = fields.Char(string='Abreviatura')
