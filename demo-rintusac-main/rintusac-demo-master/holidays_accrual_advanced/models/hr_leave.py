from odoo import models, fields


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    time_type = fields.Selection(
        related='holiday_status_id.time_type',
        store=True,
    )
    unpaid = fields.Boolean(
        related='holiday_status_id.unpaid',
        store=True,
    )
