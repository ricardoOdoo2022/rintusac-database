{
    'name': 'Absence day',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': """
    Este modulo modifica en el modulo de ausencia, la cuenta de Días entre el campo Desde al campo Hasta, 
    tomando en cuenta los días que el trabajador no presta servicio. 

    Para Perú las vacaciones son días continuos considerando días de descanso.
    """,
    'depends': ['hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_work_entry_type_data.xml',
        #'views/resource_views.xml',
        'views/wizard_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.0
}
