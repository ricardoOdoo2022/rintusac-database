{
    'name': 'Employee Service from Contracts',
    'version': '14.0.1.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'description': """
    Este modulo complementa el modulo de employee_service ya que realiza la conexión con los contratos de trabajo .
    """,
    'depends': [
        'employee_service',
        'hr_contract'
    ],
    'data': [
        'views/crons.xml',
        'views/hr_employee_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 0.00
}
