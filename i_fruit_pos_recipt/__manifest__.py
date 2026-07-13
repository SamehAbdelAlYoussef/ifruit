# -*- coding: utf-8 -*-
{
    'name': 'I Fruit Pos Recipt',
    'version': '16.0.0.1',
    'category': 'Sales/Point of Sale',
    'summary': 'I Fruit Pos Recipt',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale.assets': [
            "/i_fruit_pos_recipt/static/src/xml/OrderReceipt.xml",
            "/i_fruit_pos_recipt/static/src/css/order_recipt.css",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
    'external_dependencies': {},
}