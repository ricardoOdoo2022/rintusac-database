{
    'name': 'Holiday Process',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': """
Crea una pestaña en empleados llamada ""Vacaciones y asignaciones"" la cual nos muestra un resumen de las vacaciones ganadas, gozadas y pendiente del trabajdor.
Adicional crea un botón para generar las asignaciones de los trabajadores y así poder calcular de manera proporcional las vacaciones de los trabajadores.
    """,
    'depends': [
        'employee_service_contract',
        'holidays_accrual_advanced',
        'hr_payroll',
        'hr_work_entry_holidays',
        'automatic_leave_type'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_work_entry_type_data.xml',
        'data/hr_leave_type_data.xml',
        'views/hr_views.xml',
        'views/wizard_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.00
}