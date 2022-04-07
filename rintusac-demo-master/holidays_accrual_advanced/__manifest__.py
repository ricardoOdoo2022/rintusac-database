{
    'name': 'Advanced Accrual Allocation',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    "description": """
Es una calculadora de asignaciones, las cuales configuras deacuerdo a la necesidad del calculo que necesitas 
programar automaticamente, esta calculadora se encuentra en el modulo de ausencia/asiganciones.
    """,
    'depends': ['hr_holidays'],
    'data': [
        'security/hr_holidays_accrual_security.xml',
        'security/ir.model.access.csv',
        'wizards/hr_leave_allocation_accrual_calculator.xml',
        'views/hr_leave_allocation.xml',
        'views/hr_leave_allocation_accruement.xml',
    ],
    'installable': True,
    'auto_install': False,
}
