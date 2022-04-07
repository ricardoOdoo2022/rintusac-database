from odoo import models, fields, api


class RatesFifthRent(models.Model):
    _name = 'rates.fifth_rent'
    _description = 'Porcentaje Renta de 5ta'

    date_from = fields.Date(
        string='Desde',
        required=True
    )
    date_to = fields.Date(
        string='Hasta',
        required=True
    )
    rate_line_ids = fields.One2many(
        comodel_name='rates.fifth_rent.line',
        inverse_name='rate_parent_id',
        string='Porcentajes',
        copy=True
    )

    def name_get(self):
        return [(obj.id, '{} - {}'.format(obj.date_from.strftime('%d/%m/%Y'), obj.date_to.strftime('%d/%m/%Y'))) for obj in self]


class RatesFifthRentLine(models.Model):
    _name = 'rates.fifth_rent.line'
    _description = 'Porcentaje Renta de 5ta - Línea'
    _order = 'sequence asc'

    sequence = fields.Integer(
        string='Secuencia',
        default=1
    )
    rate_parent_id = fields.Many2one(
        comodel_name='rates.fifth_rent',
        ondelete='cascade',
        string='Porcentaje renta 5ta'
    )
    name = fields.Char(
        string='Tramo',
        required=True
    )
    value_from = fields.Integer(
        string='Rango(Desde)',
        required=True
    )
    value_to = fields.Integer(
        string='Rango(Hasta)',
        required=True
    )
    amount_from = fields.Float(
        string='Importe(Desde)',
        readonly=True
    )
    amount_to = fields.Float(
        string='Importe(Hasta)',
        readonly=True
    )
    percent = fields.Float(
        string='Porcentaje',
        required=True
    )

    @api.model
    def create(self, values):
        values = self.set_amount_per_record(values)
        return super(RatesFifthRentLine, self).create(values)

    def write(self, values):
        values = self.set_amount_per_record(values)
        return super(RatesFifthRentLine, self).write(values)

    def set_amount_per_record(self, values):
        rmv_id = self.env['various.data.uit'].search([('is_active', '=', True)], limit=1)
        if rmv_id:
            amount = rmv_id.uit_amount
            if values.get('value_from'):
                values['amount_from'] = values['value_from'] * amount
            if values.get('value_to'):
                values['amount_to'] = values['value_to'] * amount
        return values
