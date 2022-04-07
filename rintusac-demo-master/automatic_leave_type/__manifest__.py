{
    'name': 'Automatic leave type',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': 'Este módulo importa los tipos de ausencias que existen en la Planilla Electronica del Perú.',
    'depends': [
        'hr_payroll',
        'project_timesheet_holidays',
        'hr_work_entry_holidays'
    ],
    'data': [
        'data/hr_work_entry_type_data.xml',
        'data/hr_leave_type_data.xml',
        'views/hr_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.00
}
