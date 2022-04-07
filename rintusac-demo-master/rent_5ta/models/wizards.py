from odoo import models, fields, api
from odoo.exceptions import ValidationError
import datetime


class PayrollProjectionWizard(models.TransientModel):
    _name = 'payroll.projection.wizard'
    _description = 'Generador de Renta de 5ta'

    date_from = fields.Date(
        string='Desde',
        required=True
    )
    date_to = fields.Date(
        string='Hasta',
        required=True
    )
    projection_type = fields.Selection(
        selection=[
            ("last_month", "Mes anterior"),
            ("contract", "Contrato"),
            ("current_month", "Usar Información mes actual")
        ],
        string=u"Tipo de proyección",
        required=True
    )
    employees_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Empleados'
    )
    select_employee = fields.Boolean(
        string='Especificar empleado'
    )
    cancel_rent = fields.Boolean(
        string='Baja renta de 5ta'
    )

    def calc_rent_5ta(self):
        if self.select_employee and not self.employees_ids:
            raise ValidationError('Necesita seleccionar empleados.')
        if self.date_from.strftime('%Y') != self.date_to.strftime('%Y'):
            raise ValidationError('La fechas del periodo deben pertenecer al mismo año.')

        employees = []
        if self.select_employee and self.employees_ids:
            employees = self.employees_ids
        if not self.select_employee:
            employees_1 = self.env['hr.employee'].search([
                ('active', '=', True)
            ])
            for emp in employees_1:
                hr = self.env['hr.contract'].search([
                    ('employee_id', '=', emp.id),
                    ('state', '=', 'open'),
                ], limit=1)
                if hr:
                    employees.append(emp)

        # reuse methods from payslip's rule
        start_m = int(self.date_from.strftime('%m'))
        end_m = int(self.date_to.strftime('%m'))
        year = int(self.date_from.strftime('%Y'))
        first_day = datetime.date(year, 1, 1)
        last_day = datetime.date(year, 12, 31)

        hr_payslip_line = self.env['hr.payslip.line']
        periods = hr_payslip_line._get_periods(start_m, year, end_m, year)

        for employee in employees:
            projection_model = self.env['payroll.projection']
            projection_id = projection_model.search([
                ('employee_id', '=', employee.id),
                ('date_from', '=', first_day),
                ('date_to', '=', last_day),
            ])
            if not projection_id:
                projection_id = projection_model.create({
                    'employee_id': employee.id,
                    'date_from': first_day,
                    'date_to': last_day
                })
            if projection_id.state == 'closed':
                continue
            # crea lineas de las tasas de renta 5ta
            rates_id = self.env['rates.fifth_rent'].search([
                ('date_from', '<=', self.date_from),
                ('date_to', '>=', self.date_to)
            ], limit=1)
            if rates_id:
                self.create_rate_lines_rent(projection_id, 'r1', rates_id, 40)
                self.create_rate_lines_rent(projection_id, 'r2', rates_id, 150)

            # calcula y actualiza la informacion de las lineas
            self.get_amount_rem_computable(employee, projection_id, periods)
            self.get_amount_others(employee, projection_id, periods)
            self.get_amount_rem_computable_mensual(projection_id, periods)
            self.get_amount_total_rem_proy_periodo(projection_id, periods)
            self.get_amount_rem_meses_anteriores(projection_id, periods, employee)
            self.get_amount_grati(employee, projection_id, periods)

            self.get_amount_total_anual_proyectado(projection_id, periods)
            self.get_amount_ded_7uits(projection_id, periods)

            self.get_amount_total_renta_anual_proyectada(projection_id, periods)
            self.get_calc_lines_rates_r1(projection_id, periods)
            self.get_amount_renta_neta(projection_id, periods)
            self.get_amount_bono_extra(employee, projection_id, periods)
            self.get_amount_utilidades(employee, projection_id, periods)
            self.get_amount_total_renta_neta(projection_id, periods)

            self.get_calc_lines_rates_r2(projection_id, periods)
            self.get_amount_rem_ordinarias(projection_id, periods)
            self.get_amount_retenciones_meses_ant(projection_id, periods, employee)
            self.get_amount_tot_renta_anual_proyectado(projection_id, periods)

            self.get_amount_retencion_afectada_extraordinarias(projection_id, periods)

            self.get_amount_retencion_1(projection_id, periods)
            self.get_amount_retencion_total(projection_id, periods)
            self.get_amount_devolucion_impuesto_retenido(projection_id, periods)

        tree_view = self.env.ref('rent_5ta.payroll_projection_tree_view').id
        form_view = self.env.ref('rent_5ta.payroll_projection_form_view').id
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Renta 5ta',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'payroll.projection',
            'target': 'current',
            'views': [
                (tree_view, 'tree'),
                (form_view, 'form'),
            ],
            'view_id': tree_view,
        }
        return action

    def create_rate_lines_rent(self, projection_id, type_rate_rent, rate_id, start_sequence):
        projection_model_line = self.env['payroll.projection.line']

        line_ids = projection_id.line_ids.filtered(
            lambda x: x.rate_line_id and x.type_rate_rent == type_rate_rent)
        projection_line_ids = line_ids.mapped('rate_line_id.id')
        rate_line_ids = rate_id.rate_line_ids.filtered(lambda x: x.id not in projection_line_ids)
        list(map(lambda x: projection_model_line.create(
            {'name': x.name, 'projection_id': projection_id.id, 'rate_line_id': x.id,
             'sequence': start_sequence + x.sequence, 'type_rate_rent': type_rate_rent}), rate_line_ids))

    # verified if the rule is related with the referenced fifth rent's line and add this amount
    @staticmethod
    def get_amount_validate_rule_exception(payslip, name_exception):
        total = 0
        for line in payslip.line_ids:
            if line.salary_rule_id.exception_ids.filtered(lambda x: x in name_exception):
                total += line.amount
        return total

    # verified if the rule is related with the referenced fifth rent's line and get the qty of lines
    @staticmethod
    def get_qty_validate_rule_exception(payslip, name_exception):
        total = 0
        for line in payslip.line_ids:
            if line.salary_rule_id.exception_ids.filtered(lambda x: x in name_exception):
                total += 1
        return total

    # verified if a key exist inside a dict's list. Filter and mapped failed.
    @staticmethod
    def filter_data(data, key):
        new_data = []
        for rec in data:
            if rec.get(key):
                new_data.append(rec)
        return new_data

    # sum 2 two dicts with the same key
    @staticmethod
    def sum_dict_data(dict1, dict2, r_id):
        for rec in dict1:
            if rec.get(r_id):
                for key in dict2[r_id]:
                    if key in rec[r_id]:
                        rec[r_id][key] = dict2[r_id][key] + rec[r_id][key]
                        rec[r_id][key] = float('%.2f' % rec[r_id][key])
                    else:
                        rec[r_id][key] = dict2[r_id][key]
                        rec[r_id][key] = float('%.2f' % rec[r_id][key])
        return dict1

    def get_calc_per_month_project_line(self, line_name, projection_id, month):
        """
        :param line_name: Identifier of rent 5ta line
        :param projection_id: Identifier of rent 5ta
        :param month: Specific month get value in line
        :return: Get value of rent 5ta on specific line in payslip month
        """
        name_exception = self.env.ref(line_name, False)
        projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
        if not name_exception or not projection_line:
            return 0
        value = self.get_value_per_month(projection_line, month)
        return value

    def get_calc_per_month_project_line_rates(self, projection_id, month, type_rate_rent):
        projection_lines = projection_id.line_ids.filtered(
            lambda x: x.rate_line_id and x.type_rate_rent == type_rate_rent)
        value = 0
        for rate_line in projection_lines:
            value += self.get_value_per_month(rate_line, month)
        return value

    def update_dict_data(self, projection_line, month, total, data, integer=False):
        value = self.get_dict_per_month(projection_line, month, total, integer)
        if value:
            exist_list = self.filter_data(data, projection_line.id)
            if not exist_list:
                data.append(value)
            else:
                data = self.sum_dict_data(data, value, projection_line.id)
        return data

    @staticmethod
    def get_value_per_month(projection_line, month):
        value = 0
        if month == '01':
            value = projection_line.january_amount or 0.0
        elif month == '02':
            value = projection_line.february_amount or 0.0
        elif month == '03':
            value = projection_line.march_amount or 0.0
        elif month == '04':
            value = projection_line.april_amount or 0.0
        elif month == '05':
            value = projection_line.may_amount or 0.0
        elif month == '06':
            value = projection_line.june_amount or 0.0
        elif month == '07':
            value = projection_line.july_amount or 0.0
        elif month == '08':
            value = projection_line.august_amount or 0.0
        elif month == '09':
            value = projection_line.september_amount or 0.0
        elif month == '10':
            value = projection_line.october_amount or 0.0
        elif month == '11':
            value = projection_line.november_amount or 0.0
        elif month == '12':
            value = projection_line.december_amount or 0.0
        return float(value)

    @staticmethod
    def set_value_per_month(projection_line, month, value):
        if month == '01':
            projection_line.january_amount = value
        elif month == '02':
            projection_line.february_amount = value
        elif month == '03':
            projection_line.march_amount = value
        elif month == '04':
            projection_line.april_amount = value
        elif month == '05':
            projection_line.may_amount = value
        elif month == '06':
            projection_line.june_amount = value
        elif month == '07':
            projection_line.july_amount = value
        elif month == '08':
            projection_line.august_amount = value
        elif month == '09':
            projection_line.september_amount = value
        elif month == '10':
            projection_line.october_amount = value
        elif month == '11':
            projection_line.november_amount = value
        elif month == '12':
            projection_line.december_amount = value

    @staticmethod
    def get_dict_per_month(projection_line, month, value, integer):
        sub_dict = False
        if integer:
            value = int(value)
        else:
            value = float('%.2f' % value)
        if month == '01':
            sub_dict = {'january_amount': value}
        elif month == '02':
            sub_dict = {'february_amount': value}
        elif month == '03':
            sub_dict = {'march_amount': value}
        elif month == '04':
            sub_dict = {'april_amount': value}
        elif month == '05':
            sub_dict = {'may_amount': value}
        elif month == '06':
            sub_dict = {'june_amount': value}
        elif month == '07':
            sub_dict = {'july_amount': value}
        elif month == '08':
            sub_dict = {'august_amount': value}
        elif month == '09':
            sub_dict = {'september_amount': value}
        elif month == '10':
            sub_dict = {'october_amount': value}
        elif month == '11':
            sub_dict = {'november_amount': value}
        elif month == '12':
            sub_dict = {'december_amount': value}
        if not sub_dict:
            return False
        value = {projection_line.id: sub_dict}
        return value

    @api.model
    def get_contract(self, employee, date_to, date_from):
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final)

    @staticmethod
    def get_date_start(month, year):
        date_start = '{}/{}'.format(month, year)
        return date_start

    def update_project_line_records(self, data):
        if data:
            data = list(map(lambda y: list(y.items())[0], data))
            list(map(lambda x: self.env['payroll.projection.line'].browse(x[0]).write(x[1]), data))

    def get_calc_lines_rates(self, projection_id, periods, line_id, type_rate_rent):
        data = []
        for period in periods:
            month = period[0:2]
            line_ids = projection_id.line_ids.filtered(lambda x: x.rate_line_id and x.type_rate_rent == type_rate_rent)
            val_renta_anual_proy = self.get_calc_per_month_project_line(line_id, projection_id, month)
            if val_renta_anual_proy > 0:
                values = 0
                line_len = len(line_ids)
                for line in line_ids:
                    total = 0
                    sequence = line.rate_line_id.sequence
                    rate_line_id = line.rate_line_id
                    # calc line 1
                    if sequence == 1:
                        if val_renta_anual_proy < rate_line_id.amount_to:
                            total = val_renta_anual_proy * rate_line_id.percent
                            values += val_renta_anual_proy
                        else:
                            total = rate_line_id.amount_to * rate_line_id.percent
                            values += rate_line_id.amount_to
                    # calc line 5
                    elif line_len == sequence:
                        if rate_line_id.amount_from < val_renta_anual_proy:
                            total = (val_renta_anual_proy - values) * rate_line_id.percent
                    else:
                        if val_renta_anual_proy > rate_line_id.amount_to:
                            val = rate_line_id.amount_to - rate_line_id.amount_from
                        else:
                            val = val_renta_anual_proy - values
                        if val < 0:
                            val = 0
                        values += val
                        total = val * rate_line_id.percent

                    data = self.update_dict_data(line, month, total, data)
            else:
                for line in line_ids:
                    data = self.update_dict_data(line, month, 0, data)
        self.update_project_line_records(data)

    def get_amount_rem_computable(self, employee, projection_id, periods):
        name_exception = self.env.ref('rent_5ta.payroll_projection_exception_01', False)
        projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
        data = []
        if self.projection_type == 'contract':
            for period in periods:
                month = period[0:2]
                date_from, date_to = self.env['hr.payslip'].get_month_day_range(period)
                contract_id = self.get_contract(employee, date_from, date_to)
                total = contract_id.wage if contract_id else 0
                if employee.children > 0:
                    rmv_id = self.env['various.data.rmv'].search([('is_active', '=', True)], limit=1)
                    if rmv_id:
                        total += rmv_id.af_amount
                data = self.update_dict_data(projection_line, month, total, data)
        else:
            for period in periods:
                month = period[0:2]
                year = period[3:]
                if self.projection_type == 'last_month':
                    last_month = "{:02d}".format(int(month) - 1)
                    date_start_l = [self.get_date_start(last_month, int(year))]
                else:
                    date_start_l = [period]
                payslip_ids = self.env['hr.payslip'].search(
                    [('employee_id', '=', employee.id), ('date_start', 'in', date_start_l), ('state', '!=', 'cancel')])
                total = 0
                for payslip in payslip_ids:
                    total += self.get_amount_validate_rule_exception(payslip, [name_exception])
                data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_others(self, employee, projection_id, periods):
        data = []
        name_exception = self.env.ref('rent_5ta.payroll_projection_exception_02', False)
        projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
        if self.projection_type == 'current_month':
            payslip_ids = self.env['hr.payslip'].search([
                ('employee_id', '=', employee.id),
                ('date_start', 'in', periods),
                ('state', '!=', 'cancel'),
            ])
            for payslip in payslip_ids:
                date_start = payslip.date_start
                month = date_start[0:2]
                total = self.get_amount_validate_rule_exception(payslip, [name_exception])
                data = self.update_dict_data(projection_line, month, total, data)

        else:
            for period in periods:
                month = period[0:2]
                year = period[3:]
                total = 0
                if self.projection_type == 'last_month':
                    last_month = "{:02d}".format(int(month) - 1)
                    date_start_l = [self.get_date_start(last_month, int(year))]

                    payslip_ids = self.env['hr.payslip'].search([
                        ('employee_id', '=', employee.id),
                        ('date_start', 'in', date_start_l),
                        ('state', '!=', 'cancel')
                    ])
                    total = 0
                    for payslip in payslip_ids:
                        total += self.get_amount_validate_rule_exception(payslip, [name_exception])
                data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_rem_computable_mensual(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            rem = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_01', projection_id, month)
            otros = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_02', projection_id,
                                                         month)
            total = rem + otros

            mensual = self.env.ref('rent_5ta.payroll_projection_exception_03', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == mensual)
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_total_rem_proy_periodo(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            total = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_03',
                                                         projection_id, month)
            if not self.cancel_rent:
                proyec_ingresos = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_04',
                                                                       projection_id, month)
                total *= proyec_ingresos

            rem = self.env.ref('rent_5ta.payroll_projection_exception_05', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == rem)
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_rem_meses_anteriores(self, projection_id, periods, employee):
        data = []
        for period in periods:
            month = period[0:2]
            last_month = "{:02d}".format(int(month) - 1)
            int_last_month = int(last_month)
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_06', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            total = 0
            data_start_list = []
            while int_last_month > 0:
                last_month = "{:02d}".format(int_last_month)
                data_start_list.append(last_month + period[2:])
                int_last_month -= 1

            payslip_ids = self.env['hr.payslip'].search([
                ('employee_id', '=', employee.id),
                ('date_start', 'in', data_start_list),
                ('state', '!=', 'cancel'),
            ])
            r1 = self.env.ref('rent_5ta.payroll_projection_exception_01', False)
            r2 = self.env.ref('rent_5ta.payroll_projection_exception_02', False)
            for payslip in payslip_ids:
                total += self.get_amount_validate_rule_exception(payslip, [r1, r2])
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_grati(self, employee, projection_id, periods):
        data = []
        name_exception = self.env.ref('rent_5ta.payroll_projection_exception_07', False)
        projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
        total = 0
        if self.cancel_rent:
            for period in periods:
                month = period[0:2]
                payslip_ids = self.env['hr.payslip'].search([
                    ('employee_id', '=', employee.id),
                    ('date_start', '=', period),
                    ('state', '!=', 'cancel'),
                ])
                for payslip in payslip_ids:
                    total += self.get_amount_validate_rule_exception(payslip, [name_exception])
                data = self.update_dict_data(projection_line, month, total, data)
        else:
            for period in periods:
                date_from, date_to = self.env['hr.payslip'].get_month_day_range(period)
                contract_id = self.get_contract(employee, date_from, date_to)

                month = period[0:2]
                last_month = "{:02d}".format(int(month) - 1)
                int_last_month = int(last_month)
                data_start_list = [month]
                while int_last_month > 0:
                    last_month = "{:02d}".format(int_last_month)
                    data_start_list.append(last_month + period[2:])
                    int_last_month -= 1

                if contract_id and contract_id[0].labor_regime_id:
                    payslip_ids = self.env['hr.payslip'].search([
                        ('employee_id', '=', employee.id),
                        ('date_start', 'in', data_start_list),
                        ('state', '!=', 'cancel'),
                    ])
                    qty = 0
                    value = 0
                    for payslip in payslip_ids:
                        qty += self.get_qty_validate_rule_exception(payslip, [name_exception])
                        value += self.get_amount_validate_rule_exception(payslip, [name_exception])

                    if contract_id[0].labor_regime_id.code != '16':
                        if contract_id[0].labor_regime_id.code == '17':
                            if qty == 0:
                                result1 = contract_id[0].wage if contract_id else 0
                                if employee.children > 0:
                                    rmv_id = self.env['various.data.rmv'].search([('is_active', '=', True)], limit=1)
                                    if rmv_id:
                                        result1 += rmv_id.af_amount
                                diff_days = 0
                                if employee.service_start_date and employee.service_start_date > projection_id.date_from:
                                    diff_days = (employee.service_start_date - projection_id.date_from).days
                                result2 = result1 / 2 / 6 / 30 * diff_days
                                total = result1 - result2
                            elif qty == 1:
                                result1 = value * 2
                                diff_days = 0
                                if 1 <= int(month) <= 6:
                                    if employee.service_start_date and employee.service_start_date > projection_id.date_from:
                                        diff_days = (employee.service_start_date - projection_id.date_from).days

                                else:
                                    first_day, _ = self.env['hr.payslip'].get_month_day_range('07' + period[2:])
                                    if employee.service_start_date and employee.service_start_date > first_day:
                                        diff_days = (employee.service_start_date - first_day).days
                                result2 = (value / 2) / 6 / 30 * diff_days
                                total = result1 - result2
                            elif qty == 2:
                                total = value
                        elif contract_id[0].labor_regime_id.code != '17':
                            if qty == 0:
                                result1 = contract_id[0].wage if contract_id else 0
                                if employee.children > 0:
                                    rmv_id = self.env['various.data.rmv'].search([('is_active', '=', True)], limit=1)
                                    if rmv_id:
                                        result1 += rmv_id.af_amount
                                result1 *= 2
                                diff_days = 0
                                if employee.service_start_date and employee.service_start_date > projection_id.date_from:
                                    diff_days = (employee.service_start_date - projection_id.date_from).days
                                result2 = result1 / 60 / 30 * diff_days
                                total = result1 - result2
                            elif qty == 1:
                                result1 = value * 2
                                diff_days = 0
                                if 1 <= int(month) <= 6:
                                    if employee.service_start_date and employee.service_start_date > projection_id.date_from:
                                        diff_days = (employee.service_start_date - projection_id.date_from).days

                                else:
                                    first_day, _ = self.env['hr.payslip'].get_month_day_range('07' + period[2:])
                                    if employee.service_start_date and employee.service_start_date > first_day:
                                        diff_days = (employee.service_start_date - first_day).days
                                result2 = (value / 2) / 60 / 30 * diff_days
                                total = result1 - result2
                            elif qty == 2:
                                total = value

                data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_total_anual_proyectado(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            total = self.get_calc_per_month_project_line(
                'rent_5ta.payroll_projection_exception_ajuste_total_ing_anual_proy', projection_id, month)
            if total == 0:
                total += self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_05', projection_id,
                                                              month)
                total += self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_06', projection_id,
                                                              month)
                total += self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_07', projection_id,
                                                              month)
                total += self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_10', projection_id,
                                                              month)
                total += self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_11', projection_id,
                                                              month)

            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_12', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)

            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_ded_7uits(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            total = 0
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_13', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            rmv_id = self.env['various.data.uit'].search([('is_active', '=', True)], limit=1)
            if rmv_id:
                total = rmv_id.uit_amount * 7
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_total_renta_anual_proyectada(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            val_tot_rem_per = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_12',
                                                                   projection_id, month)
            val_uit = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_13', projection_id,
                                                           month)
            total = 0
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_14', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)

            if val_uit < val_tot_rem_per:
                total = val_tot_rem_per - val_uit
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    # calc rates lines r1
    def get_calc_lines_rates_r1(self, projection_id, periods):
        self.get_calc_lines_rates(projection_id, periods, 'rent_5ta.payroll_projection_exception_14', 'r1')

    # calc r1
    def get_amount_retenciones_meses_ant(self, projection_id, periods, employee):
        data = []
        for period in periods:
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_total_1', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            month = period[0:2]
            data_start_list = []
            total = 0

            if month not in ['01', '02', '03']:
                last_month = "{:02d}".format(int(month) - 1)
                int_last_month = int(last_month)
                total = 0
                while int_last_month > 0:
                    last_month = "{:02d}".format(int_last_month)
                    data_start_list.append(last_month + period[2:])
                    int_last_month -= 1
            if data_start_list:
                payslip_ids = self.env['hr.payslip'].search([
                    ('employee_id', '=', employee.id),
                    ('date_start', 'in', data_start_list),
                    ('state', '!=', 'cancel'),
                ])
                for payslip in payslip_ids:
                    total += sum(line.amount for line in payslip.line_ids.filtered(lambda x: x.code == 'R5T_001'))
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_tot_renta_anual_proyectado(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            rate_lines = self.get_calc_per_month_project_line_rates(projection_id, month, 'r1')
            ret_meses_ant = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_total_1',
                                                                 projection_id, month)
            ret_otra_emp = self.get_calc_per_month_project_line(
                'rent_5ta.payroll_projection_exception_retencion_otras_empresas', projection_id, month)
            total = rate_lines - ret_meses_ant - ret_otra_emp
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_total_2', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_retencion_1(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            total = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_total_2', projection_id,
                                                         month)
            if not self.cancel_rent:
                factor = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_total_3',
                                                              projection_id, month)
                if total != 0 and factor > 0:
                    total /= factor

                if total < 0:
                    total = 0

            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_total_4', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            data = self.update_dict_data(projection_line, month, total, data, integer=True)
        self.update_project_line_records(data)

    # calc r2
    def get_amount_renta_neta(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            total = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_14', projection_id,
                                                         month)
            if total < 0:
                total = 0
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_r2_1', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_bono_extra(self, employee, projection_id, periods):
        data = []
        name_exception = self.env.ref('rent_5ta.payroll_projection_exception_08', False)
        projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
        for period in periods:
            total = 0
            payslip_ids = self.env['hr.payslip'].search([
                ('employee_id', '=', employee.id),
                ('date_start', '=', period),
                ('state', '!=', 'cancel'),
            ])
            month = period[0:2]
            for payslip in payslip_ids:
                total += self.get_amount_validate_rule_exception(payslip, [name_exception])
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)
        '''
        data = []
        name_exception = self.env.ref('rent_5ta.payroll_projection_exception_08', False)
        projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
        if self.cancel_rent:
            for period in periods:
                month = period[0:2]
                bono = 0.00
                payslip_ids = self.env['hr.payslip'].search([
                    ('employee_id', '=', employee.id),
                    ('date_start', '=', period),
                    ('state', '!=', 'cancel'),
                ])
                for payslip in payslip_ids:
                    bono = sum(line.amount for line in payslip.line_ids.filtered(lambda x: x.code == 'GRAT_006'))
                data = self.update_dict_data(projection_line, month, bono, data)
        else:
            for period in periods:
                month = period[0:2]
                date_from, date_to = self.env['hr.payslip'].get_month_day_range(period)
                contract_id = self.get_contract(employee, date_from, date_to)
                grati = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_07', projection_id, month)
                bono = 0.00
                if contract_id and contract_id[0].labor_regime_id:
                    if contract_id[0].labor_regime_id.code != '16':
                        if contract_id[0].employee_id.health_regime_id.code == '00':
                            bono = grati * 0.09
                        elif contract_id[0].employee_id.health_regime_id.code == '01':
                            bono = grati * 0.0675

                data = self.update_dict_data(projection_line, month, bono, data)
        self.update_project_line_records(data)
        '''

    def get_amount_utilidades(self, employee, projection_id, periods):
        data = []
        name_exception = self.env.ref('rent_5ta.payroll_projection_exception_09', False)
        projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
        for period in periods:
            total = 0
            payslip_ids = self.env['hr.payslip'].search([
                ('employee_id', '=', employee.id),
                ('date_start', '=', period),
                ('state', '!=', 'cancel'),
            ])
            month = period[0:2]
            for payslip in payslip_ids:
                total += self.get_amount_validate_rule_exception(payslip, [name_exception])
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    def get_amount_total_renta_neta(self, projection_id, periods):
        data = []
        name_exception = self.env.ref('rent_5ta.payroll_projection_exception_r2_2', False)
        projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
        for period in periods:
            month = period[0:2]
            renta_neta = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_r2_1',
                                                              projection_id, month)
            bono_extra = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_08', projection_id,
                                                              month)
            utilidades = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_09', projection_id,
                                                              month)
            total = renta_neta + bono_extra + utilidades
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)

    # calc rates lines r2
    def get_calc_lines_rates_r2(self, projection_id, periods):
        self.get_calc_lines_rates(projection_id, periods, 'rent_5ta.payroll_projection_exception_r2_2', 'r2')

    def get_amount_rem_ordinarias(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            rate_lines = self.get_calc_per_month_project_line_rates(projection_id, month, 'r1')
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_total_r2_1', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            data = self.update_dict_data(projection_line, month, rate_lines, data)
        self.update_project_line_records(data)

    def get_amount_retencion_afectada_extraordinarias(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            rate_lines = self.get_calc_per_month_project_line_rates(projection_id, month, 'r2')

            rem_ordinarias = self.get_calc_per_month_project_line('rent_5ta.payroll_projection_exception_total_r2_1',
                                                                  projection_id, month)
            total = rate_lines - rem_ordinarias
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_total_r2_2', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            data = self.update_dict_data(projection_line, month, total, data, integer=True)
        self.update_project_line_records(data)

    def get_amount_retencion_total(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]
            retencion_ordinarias = self.get_calc_per_month_project_line(
                'rent_5ta.payroll_projection_exception_total_r2_2', projection_id, month)
            retencion_r1 = self.get_calc_per_month_project_line(
                'rent_5ta.payroll_projection_exception_total_4', projection_id, month)

            total = retencion_ordinarias + retencion_r1
            if total < 0:
                total = 0
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_total_r2_3', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            data = self.update_dict_data(projection_line, month, total, data, integer=True)
        self.update_project_line_records(data)

    def get_amount_devolucion_impuesto_retenido(self, projection_id, periods):
        data = []
        for period in periods:
            month = period[0:2]

            total = self.get_calc_per_month_project_line(
                'rent_5ta.payroll_projection_exception_total_ajuste_dev_imp_exceso', projection_id, month)
            if total == 0:
                retencion_meses_ant = self.get_calc_per_month_project_line(
                    'rent_5ta.payroll_projection_exception_total_1', projection_id, month)
                if retencion_meses_ant > 0:
                    rate_lines = self.get_calc_per_month_project_line_rates(projection_id, month, 'r1')

                    if rate_lines < retencion_meses_ant:
                        total = retencion_meses_ant - rate_lines
            name_exception = self.env.ref('rent_5ta.payroll_projection_exception_total_5', False)
            projection_line = projection_id.line_ids.filtered(lambda x: x.exception_id == name_exception)
            data = self.update_dict_data(projection_line, month, total, data)
        self.update_project_line_records(data)
