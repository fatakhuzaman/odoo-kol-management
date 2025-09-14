from odoo import models, fields

class KolPlatform(models.Model):
    _name = "kol.platform"
    _description = "KOL Platform"

    name = fields.Char(string="Platform", required=True)
    base_url = fields.Char(string="Base URL", help="URL before username")
    active = fields.Boolean(string="Active")
    account_ids = fields.One2many('kol.account', 'platform_id', string="Platform")

