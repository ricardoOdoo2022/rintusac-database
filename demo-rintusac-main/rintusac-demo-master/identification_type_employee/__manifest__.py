{
    'name': 'Identification type employee',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': """
Este modulo crea en empleados un campo llamado Tipo de Documento el cual le permite identificar el tipo de documento que le corresponde a sus empleados,
tambien se utiliza para poder generar varios reportes como Plame, AFP, Boletas etc.

Crea un campo llamado Nacionalidad, que ayuda a identificar a que pais pertenece el tipo de documento.
    """,
    'depends': [
        'hr',
        'l10n_latam_base'
    ],
    'data': ['views/hr_views.xml'],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.0
}
