# -*- coding: utf-8 -*-
import json
import secrets
import requests
from datetime import datetime
from datetime import timedelta
from base64 import b64encode, b64decode
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5, AES
from Crypto.Util.Padding import pad,unpad

from odoo import models, fields, api


class EinvoicingSessionManager(models.Model):
    _name = 'einvoicing.session.manager'
    _description = 'eInvoicing Session Manager'

    partner_id = fields.Many2one('res.partner')
    app_key = fields.Binary()
    token_expiry = fields.Datetime()
    auth_token = fields.Char()
    sek = fields.Binary()

    session_expiry = fields.Date()
    subscription_details = fields.Text()

    def generate_new_keys(self):
        self.partner_id.einv_txn_key = b64encode(secrets.token_bytes(16)).decode('utf-8')

    def _request_session(self,force_refresh):
        pub_key = RSA.importKey("""-----BEGIN PUBLIC KEY-----
        MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArxd93uLDs8HTPqcSPpxZ
        rf0Dc29r3iPp0a8filjAyeX4RAH6lWm9qFt26CcE8ESYtmo1sVtswvs7VH4Bjg/F
        DlRpd+MnAlXuxChij8/vjyAwE71ucMrmZhxM8rOSfPML8fniZ8trr3I4R2o4xWh6
        no/xTUtZ02/yUEXbphw3DEuefzHEQnEF+quGji9pvGnPO6Krmnri9H4WPY0ysPQQ
        Qd82bUZCk9XdhSZcW/am8wBulYokITRMVHlbRXqu1pOFmQMO5oSpyZU3pXbsx+Ox
        IOc4EDX0WMa9aH4+snt18WAXVGwF2B4fmBk7AtmkFzrTmbpmyVqA3KO2IjzMZPw0
        hQIDAQAB
        -----END PUBLIC KEY-----""")
        pub_key_encryption = PKCS1_v1_5.new(pub_key)

        self.app_key = b64encode(secrets.token_bytes(32))
        encrypted_key = b64encode(pub_key_encryption.encrypt(b64decode(self.app_key)))
        encrypted_pass = b64encode(pub_key_encryption.encrypt(bytes(self.partner_id.einv_pass, 'utf-8')))

        headers = {
            "X-CT-Auth-Token": "d07aa469-541c-449f-8d7e-629074ab5d64"
        }

        payload ={
            "data": {
                "UserName": self.partner_id.einv_user,
                "Password": encrypted_pass,
                "AppKey": encrypted_key,
                "ForceRefreshAccessToken": force_refresh
            }
        }

        url = "https://einv-gsp-sandbox.internal.cleartax.co/vital/v1.03/auth"

        response = requests.post(url, headers=headers, json=payload)
        response_json = False
        response_code = response.status_code
        if response_code == 200:
            response_json = response.json()

        print('\n\nSession Response\n',response_json)
        return response_json
        
    def _update_session(self,data):
        self.auth_token = data.get('AuthToken')
        aes = AES.new(b64decode(self.app_key), AES.MODE_ECB)
        self.sek = b64encode(unpad(aes.decrypt(b64decode(data.get('Sek'))),16))
        self.token_expiry = datetime.strptime(data.get('TokenExpiry'),'%Y-%m-%d %H:%M:%S') - timedelta(minutes=330)

    def _auth_session(self):
        try:
            current_time = fields.Datetime.now()
            session = False
            if current_time <= self.token_expiry:
                if (self.token_expiry - current_time).seconds/60 < 10:
                    session = self._request_session(True)
                else:
                    return {
                        'Success': True,
                        'Error': '',
                        'GovResponse': {}
                        }
            else:
                session = self._request_session(False)
            
            if session:
                if session.get('Status'):
                    self._update_session(session.get('Data'))
                    return {
                        'Success': True,
                        'Error': '',
                        'GovResponse': {}
                        }
                else:
                    return {
                        'Success': False,
                        'Error': 'Failed to create a valid session',
                        'GovResponse': session.get('ErrorDetails')
                        }
            else:
                return {
                    'Success': False,
                    'Error': 'Failed to create a valid session',
                    'GovResponse': {}
                }
        
        except:
            return {
                'Success': False,
                'Error': 'Unexpected error',
                'GovResponse': {}
            }
    
class EinvoicingTransactionManager(models.Model):
    _name = 'einvoicing.transaction.manager'
    _description = 'eInvoicing Transaction manager'

    session_id = fields.Many2one('einvoicing.session.manager')
    partner_id = fields.Many2one('res.partner')

    def _get_session(self,auth):
        self.partner_id = self.env['res.partner'].sudo().search([('einv_txn_key','=',auth.get('txn_key'))])
        self.session_id = self.env['einvoicing.session.manager'].search([('partner_id','=',self.partner_id.id)])
        return {
            "X-CT-Auth-Token": "d07aa469-541c-449f-8d7e-629074ab5d64",
            "user_name": self.partner_id.einv_user,
            "Gstin": self.partner_id.vat
        }
    
    def _process_irn_request(self,header,data):
        header.update({"AuthToken": self.session_id.auth_token})
        cypher = AES.new(b64decode(self.session_id.sek), AES.MODE_ECB)
        payload = {"Data":b64encode(cypher.encrypt(pad(bytes(json.dumps(data),'utf-8'),16))).decode('utf-8')}

        url = "https://einv-gsp-sandbox.internal.cleartax.co/core/v1.03/Invoice"
        response = requests.post(url, headers=header, json=payload)
        response_code = response.status_code
        if response_code == 200:
            response_json = response.json()
            if response_json.get('Status'):
                response_data = json.loads(unpad(cypher.decrypt(b64decode(response_json.get('Data'))),16).decode('utf-8'))
                return {
                    'Success': True,
                    'Error': '',
                    'GovResponse': response_data
                }
            else:
                response_data = response_json
                return {
                    'Success': False,
                    'Error': 'Invoice Error',
                    'GovResponse': response_data
                }
        else:
            return {
                'Success': False,
                'Error': 'Unable to connet to Govt Server',
                'GovResponse': {}
            }
        
    def get_irn(self,request_json):
        try:
            print('\n\nClient Request\n',request_json)
            new_rec = self.create({})
            header = new_rec._get_session(request_json.get('auth'))
        except:
            return  {
                'Success': False,
                'Error': 'Authentication Failed',
                'GovResponse': {}
            }
        if new_rec.session_id:
            session_resp = new_rec.session_id._auth_session()
            print('\n\nSession\n\n',new_rec.session_id)
            if not session_resp.get('Success'):
                print('\n\nReturn Session Response\n',session_resp)
                return session_resp
        else:
            return  {
                'Success': False,
                'Error': 'Authentication Failed',
                'GovResponse': {}
            }
        transaction_resp = new_rec._process_irn_request(header,request_json.get('data'))
        print('\n\nIRN Response\n',transaction_resp)
        return transaction_resp