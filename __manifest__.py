{
    'name': "Things Gateway",
    'summary': "Connect your Gateways with Odoo",       
    'description': """Manage the Gateways of Things in Touch""",

    'version': '11.0.5.0.210910', # update controllers.main.ThingsRasGate
    'category': 'Things',
    'website': "https://thingsintouch.com",
    'images': [
        'static/description/icon.png',
    ],
    'author': "thingsintouch.com",
    'license': 'AGPL-3',
    'application': False,
    'installable': True,    
    'depends': ['base'],
    'data': [
        'security/things_ras_security.xml',
        'security/ir.model.access.csv',
        'views/things_menus.xml',
        'views/things_ras2.xml'
    ],
# 'demo': ['demo.xml'],
}