# -*- coding: utf-8 -*-
{
    'name': "Prixgen eInvoicing Server",

    'summary': """
        Prixgen eInvoicing Server""",

    'description': """
        Prixgen eInvoicing Server
    """,

    'author': "Aniruddh Sisodia",
    'company': "Prixgen Tech Solutions Pvt. Ltd.",
    'website': "http://www.prixgen.com",

    'category': 'Integration',
    'version': '13.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/einv_manage.xml',
        'views/res_user_partner.xml',
    ],
}
