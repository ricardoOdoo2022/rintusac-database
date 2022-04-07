{
    'name': 'Basic rules',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': "Este modulo crea una serie de reglas salariales basicas para el calculo de diversos tipos de nómnas.",
    'depends': [
        'automatic_functions_rule',
        'filter_payroll',
        'various_data',
        'judicial_retention_fields',
        'types_system_pension',
        'life_insurance_management',
        'payment_conditions'
    ],
    'data': [
        'data/hr_payroll_structure_data.xml',
        'data/hr_payslip_input_type_data.xml',
        'data/hr_salary_rule_category_data.xml',
        'data/hr_salary_rule_data.xml',
        'views/hr_views.xml',
        'views/res_config_settings_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.0
}
