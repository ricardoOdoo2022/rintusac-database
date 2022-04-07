{
    'name': 'Renta de quinta',
    'version': '14.0.1.1.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': 'Se encarga de crear un modelo completo para el cálculo de renta de quinta, considerando todos los parametros establecidos por SUNAT.',
    'depends': [
        'basic_rule',
        'additional_fields_voucher',
        'employee_service_contract'
    ],
    'data': [
        'data/hr_data.xml',
        'data/payroll_projection_exception_data.xml',
        'security/ir.model.access.csv',
        'views/hr_views.xml',
        'views/payroll_projection_views.xml',
        'views/rate_fifth_rent_views.xml',
        'views/reports.xml',
        'views/wizards.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.00
}
