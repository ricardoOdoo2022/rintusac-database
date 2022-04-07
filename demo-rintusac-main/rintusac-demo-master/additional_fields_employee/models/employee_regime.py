from odoo import models, fields


class EmployeeRegime(models.Model):
    _name = 'employee.regime'
    _description = 'Régimen Laboral'

    code = fields.Char(string='Código')
    regime_description = fields.Char(string='Descripción')
    name = fields.Char(string='Abreviatura')
    private_sector = fields.Boolean(string='Sector privado')
    public_sector = fields.Boolean(string='Sector público')
    other_entities = fields.Boolean(string='Otra entidades')
    is_mype = fields.Boolean(string='¿Es MYPE?')
