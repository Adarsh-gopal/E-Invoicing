from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    einv_user = fields.Char('eInvocing Username')
    einv_pass = fields.Char('eInvocing Password')
    einv_client_id = fields.Char('Client ID')
    einv_client_secret = fields.Char('Client Secret')
    einv_sub_key = fields.Char('eInvoicing Subscription Key')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    einv_session_id = fields.Many2one('einvoicing.session.manager')
    einv_txn_key = fields.Char()