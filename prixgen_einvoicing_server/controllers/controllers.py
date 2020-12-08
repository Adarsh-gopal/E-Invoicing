# -*- coding: utf-8 -*-
# from odoo import http


# class PrixgenEinvoicingServer(http.Controller):
#     @http.route('/prixgen_einvoicing_server/prixgen_einvoicing_server/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prixgen_einvoicing_server/prixgen_einvoicing_server/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('prixgen_einvoicing_server.listing', {
#             'root': '/prixgen_einvoicing_server/prixgen_einvoicing_server',
#             'objects': http.request.env['prixgen_einvoicing_server.prixgen_einvoicing_server'].search([]),
#         })

#     @http.route('/prixgen_einvoicing_server/prixgen_einvoicing_server/objects/<model("prixgen_einvoicing_server.prixgen_einvoicing_server"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prixgen_einvoicing_server.object', {
#             'object': obj
#         })
