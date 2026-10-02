# -*- coding: utf-8 -*-
{
    'name': 'Ifruit POS Access Control',
    'version': '19.0.1.0.0',
    'summary': 'Restrict POS backend menus to managers only',
    'author': 'Noptechs',
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_menu_access.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
