from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LifeInsurance(models.Model):
    _name = 'life.insurance'
    _description = 'Vida ley'

    name = fields.Char(
        string='Entidad',
        required=True
    )
    nro = fields.Char(string='N° Póliza', required=True)
    start_date = fields.Date(string='Fecha inicio vigencia', required=True)
    end_date = fields.Date(string='Fecha fin vigencia', required=True)
    hiring_term = fields.Char(string='Plazo de contratación')
    rate = fields.Float(
        string='Tasa',
        digits=(16, 4), required=True)
    amount = fields.Float(string='Importe', required=True)
    employees_ids = fields.One2many(
        comodel_name='hr.employee',
        inverse_name='life_insurance_id',
        string='Empleados'
    )
