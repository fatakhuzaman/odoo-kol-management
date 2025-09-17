from odoo import models, fields

class KolAccount(models.Model):
    _name = "kol.account.last.post"
    _description = "KOL Account Last Post"

    account_id = fields.Many2one("kol.account", string="Account", ondelete="cascade", required=True)
    post_url = fields.Char(string="Post URL")
    views = fields.Integer(string="Views")
    likes = fields.Integer(string="Likes")
    comments = fields.Integer(string="Comments")
    shares = fields.Integer(string="Shares")
    saves = fields.Integer(string="Saves")
    post_date = fields.Datetime(string="Post Date")
