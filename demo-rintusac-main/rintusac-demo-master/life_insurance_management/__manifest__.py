{
    'name': 'Life insurance management',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': """
Este modulo crea un módelo en el módulo de localización menu Datos de nómina donde puedes administrar las 
pólizas de seguro de vida de los trabajadores.
    """,
    'depends': [
        'localization_menu',
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_views.xml',
        'views/life_insurance_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.0
}
