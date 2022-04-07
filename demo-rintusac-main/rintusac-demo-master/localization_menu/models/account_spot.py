from odoo import fields, models


class AccountSpotRetention(models.Model):
    _name = 'account.spot.retention'
    _description = 'SPOT Retención'
    name = fields.Char(
        string='Nombre',
        required=True
    )


class AccountSpotDetraction(models.Model):
    _name = 'account.spot.detraction'
    _description = 'SPOT de Detracción'
    name = fields.Char(
        string='Nombre',
        required=True
    )


class CodeAduana(models.Model):
    _name = 'code.aduana'
    _description = '[11] Código Dependencia Aduanera (Aduana)'
    name = fields.Char(
        string='Descripción',
        required=True
    )
    code = fields.Char(
        string='Código',
        required=True
    )
