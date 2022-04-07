from odoo import models, fields, api


class HolidayPetitionWizard(models.TransientModel):
    _inherit = 'holiday.petition.wizard'

    holiday_status_id = fields.Many2one(
        comodel_name='hr.leave.type',
        string='Tipo de Ausencia',
        default=lambda self: self.env.ref('holiday_process.hr_leave_type_23'),
        required=True,
        readonly=False
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HolidayPetitionWizard, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            leave1 = self.env.ref('holiday_process.hr_leave_type_23')
            leave2 = self.env.ref('holiday_sale.hr_leave_type_90')
            res['fields']['holiday_status_id']['domain'] = [('id', 'in', [leave1.id, leave2.id])]
        return res
