{
    'name': 'Various data',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': """
Crea distintos modelos en el modulo de localización tales como:
Remuneracón minima vital, UIT, SIS, SCTR.
Los cuales nos ayudan a tener actualizado los porcentajes e importes por periodos.
    """,
    'depends': ['localization_menu'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_views.xml',
        'views/various_data_rmv_views.xml',
        'views/various_data_sctr_views.xml',
        'views/various_data_sis_views.xml',
        'views/various_data_uit_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.0
}
