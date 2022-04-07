from odoo import api, fields, models


class PensionSystem(models.Model):
    _name = 'pension.system'
    _description = 'Sistema Pensionario'

    code = fields.Char(string='Código')
    pension_system = fields.Char(string='Regimen Pensionario')
    name = fields.Char(string='Abreviatura')
    private_sector = fields.Boolean(string='Sector Privado')
    public_sector = fields.Boolean(string='Sector Público')
    other_entities = fields.Boolean(string='Otras entidades')
    cuspp = fields.Boolean(string='CUSPP')
    comis_pension_ids = fields.One2many(
        comodel_name='comis.system.pension',
        inverse_name='pension_id',
        string='Comisiones'
    )
