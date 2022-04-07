from .payroll_projection import get_months_to_update
from odoo import models, fields, api


class ReportPayslipCts(models.AbstractModel):
    _name = 'report.rent_5ta.report_payroll_projection'
    _description = 'Rent 5ta - Report'

    @api.model
    def _get_report_values(self, docids=None, data=None):
        rent_ids = self.env['payroll.projection'].browse(docids)
        periods = self._get_periods(rent_ids)
        lines = self._get_periods(rent_ids)
        return {
            'doc_ids': docids,
            'docs': rent_ids,
            'data': data,
            'doc_model': 'hr.payslip',
            'periods': periods,
            'get_lines': lines,
            'employer_sign': self.env['hr.employee'].get_employer_sign(),
            'Date': fields.date.today(),
        }

    @staticmethod
    def get_last_month_with_data(lines):
        value = {}
        for projection_line in lines:
            if projection_line.january_amount:
                value = {'january_amount': True}
            if projection_line.february_amount:
                value = {'february_amount': True}
            if projection_line.march_amount:
                value = {'march_amount': True}
            if projection_line.april_amount:
                value = {'april_amount': True}
            if projection_line.may_amount:
                value = {'may_amount': True}
            if projection_line.june_amount:
                value = {'june_amount': True}
            if projection_line.july_amount:
                value = {'july_amount': True}
            if projection_line.august_amount:
                value = {'august_amount': True}
            if projection_line.september_amount:
                value = {'september_amount': True}
            if projection_line.october_amount:
                value = {'october_amount': True}
            if projection_line.november_amount:
                value = {'november_amount': True}
            if projection_line.december_amount:
                value = {'december_amount': True}
        return value

    def get_calc_lines_rent(self, id_line, rent_id, month):
        wizard = self.env['payroll.projection.wizard']
        value = wizard.get_calc_per_month_project_line(id_line, rent_id, month)
        return value

    def get_calc_line_1(self, month, rent_id):
        value = self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_12', rent_id, month)
        value += self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_09', rent_id, month)
        value += self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_08', rent_id, month)
        return value

    def get_calc_line_2(self, month, rent_id):
        value = self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_13', rent_id, month)
        return value

    def get_calc_line_3(self, month, rent_id):
        value = self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_r2_2', rent_id, month)
        return value

    def get_calc_line_4(self, month, rent_id):
        # r1
        wizard = self.env['payroll.projection.wizard']
        value = wizard.get_calc_per_month_project_line_rates(rent_id, month, 'r1')
        # r2
        value += self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_total_r2_2', rent_id, month)
        return value

    def get_calc_line_5(self, month, rent_id):
        value = self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_total_1', rent_id, month)
        value += self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_retencion_otras_empresas', rent_id,
                                          month)
        value += self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_total_r2_3', rent_id, month)
        return value

    def get_calc_line_6(self, month, rent_id):
        value = self.get_calc_lines_rent('rent_5ta.payroll_projection_exception_total_5', rent_id, month)
        return value

    @staticmethod
    def get_formatted_date():
        date_now = fields.Date.today()
        str_date = '{} DE {} DE {}'.format(date_now.strftime('%d'), date_now.strftime('%B'), date_now.strftime('%Y'))
        str_date = str_date.upper()
        return str_date

    def _get_periods(self, rent_ids):
        lines = {}
        for rent in rent_ids:
            values = self.get_last_month_with_data(rent.line_ids)
            month = get_months_to_update(values)
            year = rent.date_from.strftime('%Y')
            new_date = '{}/{}'.format(month[0], year)
            _, last_date = self.env['hr.payslip'].get_month_day_range(new_date)
            period = '{} - {}'.format(rent.date_from, last_date)
            lines.update({rent.id: {
                'period': period,
                'line_1': self.get_calc_line_1(month[0], rent),
                'line_2': self.get_calc_line_2(month[0], rent),
                'line_3': self.get_calc_line_3(month[0], rent),
                'line_4': self.get_calc_line_4(month[0], rent),
                'line_5': self.get_calc_line_5(month[0], rent),
                'line_6': self.get_calc_line_6(month[0], rent),
                'today': self.get_formatted_date()
            }})
        return lines
