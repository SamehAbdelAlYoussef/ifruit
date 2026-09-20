# -*- coding: utf-8 -*-
{
    'name': 'Ifruit Daily Branch Report',
    'version': '19.0.1.0.0',
    'summary': 'Daily POS branch balance report for Ifruit',
    'author': 'Noptechs',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'reports/daily_branch_report.xml',
        'views/wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
