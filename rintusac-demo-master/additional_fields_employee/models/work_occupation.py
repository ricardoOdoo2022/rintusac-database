from odoo import models, fields


class WorkOccupation(models.Model):
    _name = 'work.occupation'
    _description = 'Ocupación Laboral'

    code = fields.Char(string='Código')
    name = fields.Char(string='Nombre')
    executive = fields.Boolean(string='Ejecutivo')
    employee = fields.Boolean(string='Empleado')
    worker = fields.Boolean(string='Obrero')
