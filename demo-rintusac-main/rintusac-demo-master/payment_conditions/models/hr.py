from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    special_situation_id = fields.Many2one(
        comodel_name='special.situation',
        string='Situación Especial'
    )
    payment_type_id = fields.Many2one(
        comodel_name='payment.type',
        string='Tipo de pago'
    )
    variable_payment_id = fields.Many2one(
        comodel_name='variable.payment',
        string='Remuneración Variable'
    )
    schedule_pay = fields.Many2one(
        comodel_name='payment.period',
        related='structure_type_id.default_struct_id.schedule_pay'
    )


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    default_schedule_pay = fields.Many2one(
        comodel_name='payment.period',
        string='Default Scheduled Pay',
        default=lambda self: self.env.ref('payment_conditions.payment_period_1', False),
        help="Defines the frequency of the wage payment."
    )


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    schedule_pay = fields.Many2one(
        comodel_name='payment.period',
        string='Scheduled Pay',
        default=lambda self: self.env.ref('payment_conditions.payment_period_1', False),
        help="Defines the frequency of the wage payment."
    )
