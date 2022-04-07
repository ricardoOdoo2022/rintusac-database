{
    'name': 'Additional fields employee',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': """
Este modulo crea diversos campos en el contrato de trabajo, que existen en T- Registro tales como:
 - Regimen Laboral
 - Discapacidad
 - Condicion Laboral
 - Jornada de trabajo
 - Jornada acumulativa
 - Trabajo en horario nocturno
 - Sindicalizado 
""",
    'depends': [
        'hr_contract',
        'localization_menu'
    ],
    'data': [
        'data/academic_degree_data.xml',
        'data/employee_regime_data.xml',
        'data/type_contract_data.xml',
        'data/work.occupation.csv',
        'views/academic_degree_views.xml',
        'views/employee_regime_views.xml',
        'views/health_regime_views.xml',
        'views/hr_views.xml',
        'views/type_contract_views.xml',
        'views/work_occupation_views.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
}
