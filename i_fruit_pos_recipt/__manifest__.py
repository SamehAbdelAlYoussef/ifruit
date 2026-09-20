# -*- coding: utf-8 -*-
{
    'name': 'I Fruit Pos Recipt report',
    'version': '19.0.0.1',
    'category': 'Sales/Point of Sale',
    'summary': 'I Fruit Pos Recipt',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'i_fruit_pos_recipt/static/src/app/screens/receipt_screen/receipt/**/*',
            'i_fruit_pos_recipt/static/src/css/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {},
}







