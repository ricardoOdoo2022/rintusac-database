from odoo import api, fields, models


class TopeAFP(models.Model):
    _name = 'tope.afp'
    _description = 'Tope AFP'

    date_from = fields.Date(
        string='Desde',
        required=True
    )
    date_to = fields.Date(
        string='Hasta',
        required=True
    )
    top = fields.Float(string='Tope')

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s - %s] %s" % (rec.date_from or '', rec.date_to or '', rec.top)))
        return result
