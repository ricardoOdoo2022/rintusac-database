from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_employer = fields.Boolean(
        string='Es Empleador',
        groups="hr.group_hr_user"
    )
    employer_sign = fields.Image(
        string='Firma del empleador',
        copy=False,
        attachment=True,
        max_width=128, max_height=128,
        help='Firma del empleador, se visualizará en las boletas de los trabajadores'
    )

    @api.onchange('is_employer')
    def onchange_is_employer(self):
        if not self.is_employer:
            self.employer_sign = False

    def get_employer_sign(self):
        sign = self.env['hr.employee'].search([('is_employer', '=', True), ('employer_sign', '!=', False)], limit=1)
        values = {}
        if sign:
            values.update({
                'name': sign.name.upper(),
                'job_title': sign.job_title.upper() if sign.job_title else '',
                'sign': sign.employer_sign,
                'sign_decode': sign.employer_sign.decode('utf-8'),
                'type_identification_id': sign.type_identification_id.name.upper() if sign.type_identification_id else '',
                'identification_id': sign.identification_id or ''
            })
        return values


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    law = fields.Text(string='Ley/Decretos')
