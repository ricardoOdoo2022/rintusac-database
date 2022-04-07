{
    'name': 'Types system pension',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': """
Este modulo crea en el modulo de Localización un menu de tipo de sistema de pensiones donde estan todas las registradas en el Perú, adicional se pueden administrar las comisiones de cada sistema de pensiones y los topes correspondentes.
Esta información se muestra en hr.employee para asignar a cada trabajador y se pueda realizar su calculo en cada paylip.
""",
    'depends': [
        'localization_menu',
        'hr_contract'
    ],
    'data': [
        'data/pension_system_data.xml',
        'views/comis_system_pension_views.xml',
        'views/hr_views.xml',
        'views/pension_system_views.xml',
        'views/tope_afp_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.0
}
