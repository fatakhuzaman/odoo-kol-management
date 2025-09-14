from odoo import models, fields

class KolNiche(models.Model):
    _name = "kol.niche"
    _description = "KOL Niche"

    name = fields.Char(string="Niche", required=True)
    active = fields.Boolean(string="Active")
    account_ids = fields.Many2many('kol.account', 'niche_id', string="Niche")