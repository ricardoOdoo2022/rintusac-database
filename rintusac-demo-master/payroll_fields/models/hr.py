from dateutil.relativedelta import relativedelta
from lxml import etree
from odoo import models, fields, api


def set_filter_six_month_before(self, res):
    doc = etree.XML(res['arch'])
    for node in doc.xpath("//filter[@name='six_month_before']"):
        date_now = fields.Date.today()
        hr_payslip = self.env['hr.payslip']
        hr_payslip_line = self.env['hr.payslip.line']
        date_start, year, month, _ = hr_payslip.generate_date_start_month_year(date_now, date_now)
        month = int(month)
        year = int(year)
        start_m, star_y = hr_payslip_line._get_month(year, month, 6)
        end_m, end_y = hr_payslip_line._get_month(year, month, 1)
        periods = hr_payslip_line._get_periods(start_m, star_y, end_m, end_y)
        modifiers = "[('date_start', 'in', {})]"
        modifiers = modifiers.format(periods)
        node.set('domain', modifiers)
    res['arch'] = etree.tostring(doc, encoding='unicode')
    return res


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    date_st_dt = fields.Date(
        string='Mes de nómina',
        compute='_compute_date_start'
    )

    @api.depends('date_start', 'date_end')
    def _compute_date_start(self):
        payslip = self.env['hr.payslip']
        for rec in self:
            if rec.date_start and rec.date_end:
                _, _, _, rec.date_st_dt = payslip.generate_date_start_month_year(rec.date_start, rec.date_end)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    employee_category_ids = fields.Many2many(
        comodel_name='hr.employee.category',
        string='Etiquetas empleado',
        related='employee_id.category_ids'
    )
    date_start = fields.Char(
        string='Mes/Año nómina',
        compute='_compute_date_start',
        store=True
    )
    date_start_dt = fields.Date(
        string='Mes de nómina',
        compute='_compute_date_start',
        store=True
    )
    month = fields.Char(
        string='Mes actual de nómina',
        compute='_compute_date_start',
        store=True
    )
    year = fields.Char(
        string='Año de nómina',
        compute='_compute_date_start',
        store=True
    )

    @api.depends('date_from', 'date_to')
    def _compute_date_start(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.date_start, rec.year, rec.month, rec.date_start_dt = self.generate_date_start_month_year(
                    rec.date_from, rec.date_to)

    def generate_date_start_month_year(self, date_from, date_to):
        if date_from.strftime('%m') != date_to.strftime('%m'):
            from_date = self.get_new_date(date_from, 31)
            from_days = self.number_days_per_range(from_date, date_from)

            to_date = self.get_new_date(date_to, 1)
            to_days = self.number_days_per_range(date_to, to_date)
            if from_days > to_days:
                name = date_from
            else:
                name = date_to
        else:
            name = date_to
        date_start = '{}/{}'.format(name.strftime('%m'), name.strftime('%Y'))
        year = name.strftime('%Y')
        month = name.strftime('%m')
        return date_start, year, month, name

    @staticmethod
    def number_days_per_range(start, end):
        return (start - end).days

    @staticmethod
    def get_new_date(date_from, days):
        return date_from + relativedelta(day=days)


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    date_start = fields.Char(
        string='Mes/Año nómina',
        related="slip_id.date_start"
    )
    date_start_dt = fields.Date(
        string='Mes de nómina',
        related="slip_id.date_start_dt",
        store=True
    )
    state = fields.Selection(
        string='Estado',
        related="slip_id.state",
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string="Departmento",
        related='employee_id.department_id',
    )
    disability = fields.Boolean(
        string='Discapacidad',
        related='employee_id.disability',
    )
    struct_id = fields.Many2one(
        comodel_name='hr.payroll.structure',
        string='Estructura',
        related='slip_id.struct_id',
    )

    @staticmethod
    def _get_periods(start_m, start_y, end_m, end_y):
        """
        :param start_m: Initial month of period
        :param start_y: Initial year of period
        :param end_m: Final month of period
        :param end_y: Final year of period
        :return: Return list of months between 'start_m/star_y' and 'end_m/end_y' => Ex: 08/18 12/18 = [08/18, 09/18, 10/18, 11/18, 12/18]
        """
        start = '{}/{}'.format("{:02d}".format(start_m), start_y)
        end = '{}/{}'.format("{:02d}".format(end_m), end_y)
        periods = [start]
        value = False
        if start == end:
            return periods
        while value != end:
            if start_y == end_y:
                start_m += 1
            else:
                start_m += 1
                if start_m == 13:
                    start_y += 1
                    start_m = 1
            value = '{}/{}'.format("{:02d}".format(start_m), start_y)
            periods.append(value)
        return periods

    @staticmethod
    def _get_month(year, month, value_month):
        value = month - value_month
        if value < 0:
            new_month = 12 + value
            new_year = year - 1
        elif value == 0:
            new_month = 12
            new_year = year - 1
        else:
            new_month = value
            new_year = year
        return new_month, new_year

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HrPayslipLine, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'search':
            res = set_filter_six_month_before(self, res)
        return res


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    date_from = fields.Date(
        string='Desde',
        related='payslip_id.date_from'
    )
    date_to = fields.Date(
        string='Hasta',
        related='payslip_id.date_to'
    )
    date_start = fields.Char(
        string='Mes/Año nómina',
        related='payslip_id.date_start'
    )
    date_start_dt = fields.Date(
        string='Mes de nómina',
        related='payslip_id.date_start_dt',
        store=True
    )
    employee_id = fields.Many2one(
        string='Empleado',
        related='contract_id.employee_id'
    )
    state = fields.Selection(
        default='draft',
        string='Estado',
        related='payslip_id.state'
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string="Departmento",
        related='employee_id.department_id'
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Compañia",
        related='contract_id.company_id',
    )
    disability = fields.Boolean(
        string='Discapacidad',
        related='employee_id.disability'
    )
    struct_id = fields.Many2one(
        comodel_name='hr.payroll.structure',
        string='Estructura',
        related='payslip_id.struct_id'
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HrPayslipWorkedDays, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'search':
            res = set_filter_six_month_before(self, res)
        return res


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    date_from = fields.Date(
        string='Desde',
        related='payslip_id.date_from'
    )
    date_to = fields.Date(
        string='Hasta',
        related='payslip_id.date_to'
    )
    date_start = fields.Char(
        string='Mes/Año nómina',
        related='payslip_id.date_start'
    )
    date_start_dt = fields.Date(
        string='Mes de nómina',
        related='payslip_id.date_start_dt',
        store=True
    )
    employee_id = fields.Many2one(
        string='Empleado',
        related='contract_id.employee_id'
    )
    state = fields.Selection(
        string='Estado',
        related='payslip_id.state'
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string="Departmento",
        related='employee_id.department_id'
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Compañia",
        related='contract_id.company_id',
    )
    disability = fields.Boolean(
        string='Discapacidad',
        related='employee_id.disability'
    )
    struct_id = fields.Many2one(
        comodel_name='hr.payroll.structure',
        string='Estructura',
        related='payslip_id.struct_id'
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HrPayslipInput, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'search':
            res = set_filter_six_month_before(self, res)
        return res
