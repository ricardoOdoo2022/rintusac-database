from datetime import datetime, date
from odoo import api, fields, models
import pytz


class HRContractUpdateWizard(models.TransientModel):
    _name = "hr.contract.update.wizard"
    _description = "Wizard to update fields on contracts"

    date_generated_from = fields.Date(
        string='Desde',
        required=True
    )
    date_generated_to = fields.Date(
        string='hasta',
        required=True
    )

    def action_update_hr_contract_fields(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        contract_ids = self.env['hr.contract'].browse(active_ids)
        contract_ids._generate_work_entries_specific_period(self.date_generated_from, self.date_generated_to)


class HRContract(models.Model):
    _inherit = "hr.contract"

    def action_open_hr_contract_update_wizard(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        return {
            'context': self.env.context,
            'name': 'Actualizar campos en contrato',
            'res_model': 'hr.contract.update.wizard',
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def _generate_work_entries_specific_period(self, date_start, date_stop):
        vals_list = []
        date_start_dt = fields.Datetime.to_datetime(date_start)
        date_stop_dt = datetime.combine(fields.Datetime.to_datetime(date_stop), datetime.max.time())
        for contract in self:
            if contract.date_end:
                contract_date_end = datetime.combine(fields.Datetime.to_datetime(contract.date_end), datetime.max.time())
                date_stop = contract_date_end if date_stop_dt > contract_date_end else date_stop_dt
            else:
                date_stop = date_stop_dt
            contract.write({'date_generated_to': date_stop})
            contract_date_start = fields.Datetime.to_datetime(contract.date_start)
            date_start = contract_date_start if date_start_dt < contract_date_start else date_start_dt
            vals_list.extend(contract._get_work_entries_values(date_start, date_stop))

        if not vals_list:
            return self.env['hr.work.entry']

        return self.env['hr.work.entry'].create(vals_list)


class HrWorkEntryType(models.Model):
    _inherit = 'hr.work.entry.type'

    name = fields.Char(translate=True)

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    code = fields.Char(string='Código')