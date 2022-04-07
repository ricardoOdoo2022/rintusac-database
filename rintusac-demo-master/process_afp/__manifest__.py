{
    'name': 'Process AFP',
    'version': '14.0.1.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': "",
    'depends': [
        'hr_localization_menu',
        'types_system_pension',
        'employee_service',
        'identification_type_employee',
        'personal_information'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/afp_interface_views.xml'
    ],
    'installable': True,
    'auto_install': False,
}
