from .reports import PlameReport
from odoo import api, fields, models
import base64


class PlameLines(models.Model):
    _name = 'plame.lines'
    _description = '[22] Ingresos, tributos y descuentos'

    code = fields.Char(string='CÓDIGO')
    name = fields.Char(string='DESCRIPCIÓN DE LOS INGRESOS, TRIBUTOS Y DESCUENTOS')
    essalud_seguro_regular = fields.Boolean(string='ESSALUD SEGURO REGULAR TRABAJADOR')
    essalud_cbssp = fields.Boolean(string='ESSALUD - CBSSP - SEG TRAB PESQUERO')
    essalud_seguro_agrario = fields.Boolean(string='ESSALUD SEGURO AGRARIO / ACUICULTOR')
    essalud_sctr = fields.Boolean(string='ESSALUD SCTR')
    imp_extra_solidaridad = fields.Boolean(string='IMPUESTO EXTRAORD. DE SOLIDARIDAD (8)')
    fondo_der_artista = fields.Boolean(string='FONDO DERECHOS SOCIALES DEL ARTISTA')
    senati = fields.Boolean(string='SENATI')
    sistema_nacional_pensiones = fields.Boolean(string='SISTEMA NACIONAL DE PENSIONES 19990')
    sistema_privado_pensiones = fields.Boolean(string='SISTEMA PRIVADO DE PENSIONES')
    fondo_compl_jub = fields.Boolean(string='FONDO COMPL DE JUBIL MIN, MET Y SIDER (1)')
    reg_esp_pesquero = fields.Boolean(string='RÉG.ESP. PENSIONESTRAB. PESQUERO')
    rent5ta = fields.Boolean(string='RENTA 5TA CATEGORÍA RETENCIONES')
    essalud_regular_pension = fields.Boolean(string='ESSALUD SEGURO REGULAR PENSIONISTA')
    contrib_sol_asist = fields.Boolean(string='CONTRIB. SOLIDARIA ASISTENCIA PREVIS.')


class PlameFiles(models.Model):
    _name = 'plame.files'
    _description = 'Reportes Plame'

    date_from = fields.Date(
        string='Fecha de Inicio',
        required=True
    )
    date_to = fields.Date(
        string='Fecha de Fin',
        required=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    rem_filename = fields.Char(string='Nombre archivo .rem')
    rem_binary = fields.Binary(string='.Rem')
    jor_filename = fields.Char(string='Nombre archivo .jor')
    jor_binary = fields.Binary(string='.Jor')
    snl_filename = fields.Char(string='Nombre archivo .snl')
    snl_binary = fields.Binary(string='.Sni')
    for_filename = fields.Char(string='Nombre archivo .for')
    for_binary = fields.Binary(string='.For')

    def generate_files(self):
        data_rem = self._get_data_rem()
        data_jor = self._get_data_jor()
        data_snl = self._get_data_snl()
        data_for = self._get_data_for()
        filename = self._get_filename()
        report_file = PlameReport(data_rem, data_jor, data_snl, data_for, filename, self)

        values = {
            'rem_filename': report_file.get_filename('rem'),
            'rem_binary': base64.encodebytes(report_file.get_content_rem() or '\n'.encode()),
            'jor_filename': report_file.get_filename('jor'),
            'jor_binary': base64.encodebytes(report_file.get_content_jor() or '\n'.encode()),
            'snl_filename': report_file.get_filename('snl'),
            'snl_binary': base64.encodebytes(report_file.get_content_snl() or '\n'.encode()),
            'for_filename': report_file.get_filename('for'),
            'for_binary': base64.encodebytes(report_file.get_content_for() or '\n'.encode()),
        }
        self.write(values)

    def _get_filename(self):
        code_file_plame = self.env['ir.config_parameter'].sudo().get_param('process_plame.code_file_plame', default='----')
        year = self.date_from.strftime('%Y')
        month = self.date_from.strftime('%m')
        company_vat = self.company_id.vat or '99999999'

        filename = '{}{}{}{}'.format(code_file_plame, year, month, company_vat)
        return filename

    @staticmethod
    def update_rem_data(rem_data, employee, code, amount, paid_amount):
        amount = round(amount, 2)
        paid_amount = round(paid_amount, 2)
        if amount - int(amount) == 0:
            amount = int(amount)

        if paid_amount - int(paid_amount) == 0:
            paid_amount = int(paid_amount)
        rem_data.append({
            'document_type': employee.type_identification_id.l10n_pe_vat_code[0:2] if employee.type_identification_id else '00',
            'document_number': employee.identification_id[0:15] if employee.identification_id else '00000000',
            'plame_code': code[0:4],
            'amount': amount,
            'paid_amount': paid_amount
        })
        return rem_data

    def _get_data_rem(self):
        rem_data = []
        employee_cat_id = self.env.ref('process_plame.hr_employee_category_sub', False)
        payslip_lines = self.env['hr.payslip.line'].search([
            ('date_start_dt', '>=', self.date_from),
            ('date_start_dt', '<=', self.date_to),
            ('contract_id', '!=', False),
            ('employee_id.category_ids', 'not in', employee_cat_id.id)
        ])
        employees_ids = payslip_lines.mapped('employee_id')

        for employee in employees_ids:
            codes_plame = payslip_lines.filtered(
                lambda x: x.salary_rule_id.plame_ids and x.employee_id == employee).mapped('salary_rule_id.plame_ids.code')
            extra_list_code = ['0601', '0606', '0608']
            filter_lines = payslip_lines.filtered(lambda x: x.employee_id == employee)
            if employee.pension_system_id and employee.pension_system_id.cuspp:
                for extra_code in extra_list_code:
                    if extra_code not in codes_plame:
                        rem_data = self.update_rem_data(rem_data, employee, extra_code, 0, 0)

            extra_list_code2 = ['0121', '0605']
            for extra_code in extra_list_code2:
                if extra_code not in codes_plame:
                    rem_data = self.update_rem_data(rem_data, employee, extra_code, 0, 0)

            for code in codes_plame:
                filter_codes = filter_lines.filtered(lambda x: x.salary_rule_id.plame_ids)
                amount = 0.0
                paid_amount = 0.0
                for line in filter_codes:
                    if line.salary_rule_id.plame_ids[0].code == code:
                        amount += line.amount
                        if line.slip_id.state == 'done':
                            paid_amount += line.amount

                if code in ['0602', '0608', '0609', '0611', '0613', '0614', '0615', '0617', '0618', '0801', '0803', '0805', '0807', '0809',
                            '0810', '0811', '0701', '0702', '0703', '0704', '0705', '0706', '0707']:
                    amount = 0
                if employee.pension_system_id and employee.pension_system_id.cuspp:
                    if code not in codes_plame:
                        amount = 0
                rem_data = self.update_rem_data(rem_data, employee, code, amount, paid_amount)
        return rem_data

    def _get_data_jor(self):
        jor_data = []
        employee_cat_id = self.env.ref('process_plame.hr_employee_category_sub', False)
        payslip_lines = self.env['hr.payslip'].search([
            ('date_start_dt', '>=', self.date_from),
            ('date_start_dt', '<=', self.date_to),
            ('contract_id', '!=', False),
            ('employee_id.category_ids', 'not in', employee_cat_id.id)
        ])
        employees_ids = payslip_lines.mapped('employee_id')

        for employee in employees_ids:
            filter_lines = payslip_lines.filtered(lambda x: x.employee_id == employee)
            ord_hours = 0
            hours_extra = 0

            for slip in filter_lines:
                ord_hours += sum(line.number_of_hours for line in slip.worked_days_line_ids.filtered(
                    lambda x: x.code in ['WORK100', 'GLOBAL'] or x.work_entry_type_id.is_leave))
                hours_extra += sum(line.amount for line in slip.input_line_ids.filtered(
                    lambda x: x.code in ['HE_100', 'HE_025', 'HEA_025', 'HE_035', 'HEA_035']))
            min_extra = self.convert_float_to_time(hours_extra)
            jor_data.append({
                'document_type': employee.type_identification_id.l10n_pe_vat_code[0:2] if employee.type_identification_id else '00',
                'document_number': employee.identification_id[0:15] if employee.identification_id else '00000000',
                'ord_hours': int(ord_hours) if ord_hours < 360 else 360,
                'ord_min': 0,
                'hours_extra': int(hours_extra) if hours_extra < 360 else 360,
                'min_extra': min_extra
            })
        return jor_data

    def _get_data_snl(self):
        snl_data = []
        employee_cat_id = self.env.ref('process_plame.hr_employee_category_sub', False)
        payslip_lines = self.env['hr.payslip.worked_days'].search([
            ('date_start_dt', '>=', self.date_from),
            ('date_start_dt', '<=', self.date_to),
            ('contract_id', '!=', False),
            ('employee_id.category_ids', 'not in', employee_cat_id.id)
        ])

        employees_ids = payslip_lines.mapped('employee_id')
        codes = payslip_lines.filtered(lambda x: x.work_entry_type_id.is_leave).mapped('code')
        for employee in employees_ids:
            for code in codes:
                days = sum(line.number_of_days for line in payslip_lines.filtered(lambda x: x.employee_id == employee and x.code == code))
                if days > 0:
                    snl_data.append({
                        'document_type': employee.type_identification_id.l10n_pe_vat_code[0:2] if employee.type_identification_id else '00',
                        'document_number': employee.identification_id[0:15] if employee.identification_id else '00000000',
                        'code': code[0:2],
                        'days': int(days)
                    })
        return snl_data

    def _get_data_for(self):
        for_data = []
        employee_cat_id = self.env.ref('process_plame.hr_employee_category_sub', False)
        payslip_lines = self.env['hr.payslip.line'].search([
            ('date_start_dt', '>=', self.date_from),
            ('date_start_dt', '<=', self.date_to),
            ('code', '=', 'NET'),
            ('contract_id', '!=', False),
            ('employee_id.category_ids', 'not in', employee_cat_id.id)
        ])

        practitioner_lines = payslip_lines.filtered(lambda x: x.contract_id.is_practitioner)
        employees_ids = practitioner_lines.mapped('employee_id')

        for employee in employees_ids:
            net_val = sum(line.amount for line in practitioner_lines.filtered(lambda x: x.employee_id == employee))
            net_val = round(net_val, 2)
            if net_val - int(net_val) == 0:
                net_val = int(net_val)

            for_data.append({
                'document_type': employee.type_identification_id.l10n_pe_vat_code[0:2] if employee.type_identification_id else '00',
                'document_number': employee.identification_id[0:15] if employee.identification_id else '00000000',
                'net_val': net_val
            })
        return for_data

    @staticmethod
    def convert_float_to_time(value):
        if isinstance(value, str):
            value = float(value)
        int_val = int(value)
        value = value - int_val
        new_val = (value * 60) / 10
        return int(new_val)
