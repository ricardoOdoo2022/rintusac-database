from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    cuspp = fields.Char(
        string='CUSPP',
        groups="hr.group_hr_user"
    )
    is_cuspp = fields.Boolean(
        string='CUSPP activo',
        compute='compute_is_cuspp',
        store=True,
        groups="hr.group_hr_user"
    )
    pension_system_id = fields.Many2one(
        comodel_name='pension.system',
        string='Sistema de pensiones',
        groups="hr.group_hr_user"
    )
    pension_sctr = fields.Boolean(
        string='SCTR Pensión',
        groups="hr.group_hr_user"
    )
    commission_type = fields.Selection(
        selection=[
            ('amount', 'Saldo'),
            ('flow', 'Flujo')
        ],
        string='Tipo de Comisión AFP',
        groups="hr.group_hr_user"
    )

    @api.depends('pension_system_id')
    def compute_is_cuspp(self):
        for rec in self:
            if rec.pension_system_id and rec.pension_system_id.cuspp:
                rec.is_cuspp = True
            else:
                rec.is_cuspp = False
