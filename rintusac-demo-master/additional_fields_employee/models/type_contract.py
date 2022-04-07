from odoo import models, fields


class TypeContract(models.Model):
    _name = 'type.contract'
    _description = 'Tipo de Contrato'

    code = fields.Char(string='Código')
    contract_type = fields.Char(string='Tipo de Contrato')
    name = fields.Char(string='Abreviatura')
