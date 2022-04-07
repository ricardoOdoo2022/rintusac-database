{
    'name': 'Payment Conditions',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': """
Crea en el hr.contract en la pestaña de pago los campos que describen el pago del trabajador como Tipo de pago, periocidad, situación especial.
""",
    'depends': [
        'localization_menu',
        'hr_payroll'
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/hr_views.xml',
        'views/payment_period_views.xml',
        'views/payment_type_views.xml',
        'views/special_situation_views.xml',
        'views/variable_payment_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.0
}
