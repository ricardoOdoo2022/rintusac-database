from odoo import api, fields, models


class VariousDataRMV(models.Model):
    _name = 'various.data.rmv'
    _description = 'Remuneracion minima vital'

    register_date = fields.Date(string='Fecha de registro')
    due_date = fields.Date(string='Fecha de vencimiento')
    rmv_amount = fields.Float(string='Importe RMV')
    af_amount = fields.Float(string='Importe AF')
    is_active = fields.Boolean(string='Activo')


class VariousDataSCTR(models.Model):
    _name = 'various.data.sctr'
    _description = 'Seguro Complementario de Trabajo de Riesgo'

    register_date = fields.Date(string='Fecha de registro')
    due_date = fields.Date(string='Fecha de vencimiento')
    pension_percent = fields.Float(string='Pensión %')
    health_percent = fields.Float(string='Salud %')
    pension_amount = fields.Float(string='Pensión Importe')
    health_amount = fields.Float(string='Salud Importe')
    name = fields.Char(
        string='Nombre de la entidad',
        required=True
    )
    employee_ids = fields.One2many(
        comodel_name='hr.employee',
        inverse_name='sctr_id',
        string='Empleados'
    )


class VariousDataUIT(models.Model):
    _name = 'various.data.uit'
    _description = 'Unidad Impositiva Tributaria'

    register_date = fields.Date(string='Fecha de registro')
    due_date = fields.Date(string='Fecha de vencimiento')
    uit_amount = fields.Float(string='Importe')
    is_active = fields.Boolean(string='Activo')


class VariousDataSIS(models.Model):
    _name = 'various.data.sis'
    _description = 'Seguro Integral de Salud'

    register_date = fields.Date(string='Fecha de registro')
    due_date = fields.Date(string='Fecha de vencimiento')
    sis_amount = fields.Float(string='Importe')
    is_active = fields.Boolean(string='Activo')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    sctr_id = fields.Many2one(
        comodel_name='various.data.sctr',
        string='Seguro Complementario de Trabajo de Riesgo'
    )
