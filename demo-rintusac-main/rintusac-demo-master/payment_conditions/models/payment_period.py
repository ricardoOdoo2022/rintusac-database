from odoo import api, fields, models


class PaymentPeriod(models.Model):
    _name = 'payment.period'
    _description = 'Periodicidad de la remuneración'

    code = fields.Char(string='Código')
    payment_description = fields.Char(string='Descripción')
    name = fields.Char(string='Abreviatura')
