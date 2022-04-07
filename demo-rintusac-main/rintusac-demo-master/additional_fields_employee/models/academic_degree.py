
from odoo import fields, models


class AcademicDegree(models.Model):
    _name = 'academic.degree'
    _description = 'Tipos de documento'

    code = fields.Char(string='Código')
    academic_description = fields.Char(string='Descripción')
    name = fields.Char(string='Abreviatura')
