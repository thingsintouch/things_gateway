from odoo import models, fields
from uuid import uuid4

class ThingsRoute(models.Model):
    _name = 'things.route'
    _description = 'description'

    _sql_constraints = [ (  'route_uniq',
                            'UNIQUE (route)',
                            'Route must be unique.')
                                ]

    def generate_route(self):
        result = str(fields.Datetime.now())+str(uuid4())
        result = result.replace(" ","").replace(":","").replace("-","")
        return result

    route =fields.Char(
        string = 'route',
        help = 'route to exchange data with "things"',
        default = generate_route,
        store = True,
        compute_sudo = False,
        readonly = True
        )
