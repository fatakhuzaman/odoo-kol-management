import requests

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class KolAccount(models.Model):
    _name = "kol.account"
    _description = "KOL Account"

    name = fields.Char(string="Username", required=True)
    platform_id = fields.Many2one('kol.platform', string="Platform", required=True)
    niche_id = fields.Many2many('kol.niche', string="Niche", required=True)
    followers = fields.Integer(string="Followers")
    reach = fields.Char(string="Reach")
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id.id)
    rate_card = fields.Monetary(string="Rate Card", currency_field="currency_id", required=True)
    er = fields.Float(string="ER", help="Engagement Rate")
    cpe = fields.Monetary(string="CPE", help="Cost Per Engagement", currency_field="currency_id")
    contact = fields.Char(string="Contact", required=True)
    description = fields.Text(string="Description")
    last_post_ids = fields.One2many('kol.account.last.post', 'account_id', string="Last Post")

    @api.model
    def create(self, vals_list):
        record = super(KolAccount, self).create(vals_list)
        record._fetch_apify()
        return record

    def action_refetch_apify(self):
        for rec in self:
            rec._fetch_apify()

    def _fetch_apify(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('apify.api_key')
        if not api_key:
            raise UserError("Apify API Key is not set. Add it in System Parameters (apify.api_key).")
        
        url = f"https://api.apify.com/v2/acts/clockworks~free-tiktok-scraper/run-sync-get-dataset-items?token={api_key}"
        payload = {
            "profiles": [self.name],
            "excludePinnedPosts": True,
            "resultsPerPage": 10,
        }

        resp = requests.post(url, json=payload)        
        data = resp.json()

        followers = data[0].get("authorMeta", {}).get("fans", 0)
        reach = ""
        if followers >= 10000000:
            reach = "Super Stars"
        elif followers >= 1000000:
            reach = "Mega"
        elif followers >= 100000:
            reach = "Macro"
        elif followers >= 10000:
            reach = "Micro"
        elif followers < 10000:
            reach = "Nano"
            
        like = 0
        comment = 0
        share = 0
        save = 0
        self.last_post_ids.unlink()
        last_post = []
        for i in range(len(data)):
            post = data[i]
            like += post.get("diggCount", 0)
            comment += post.get("commentCount", 0)
            share += post.get("shareCount", 0)
            save += post.get("collectCount", 0)

            post_date = False
            try:
                post_date = datetime.strptime(post.get("createTimeISO").replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    post_date = datetime.strptime(post.get("createTimeISO").replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    post_date = False

            last_post.append((0, 0, {
                "name": self.name,
                "post_url": post.get("webVideoUrl"),
                "views": post.get("playCount", 0),
                "likes": post.get("diggCount", 0),
                "comments": post.get("commentCount", 0),
                "shares": post.get("shareCount", 0),
                "saves": post.get("collectCount", 0),
                "post_date": post_date, 
            }))
            
        self.followers = followers
        self.reach = reach
        self.er = ((like + comment + share + save) / 10) / followers
        self.cpe = self.rate_card / ((like + comment + share + save) / 10)
        self.last_post_ids = last_post

    def write(self, vals):
        res = super(KolAccount, self).write(vals)

        for rec in self:
            if 'rate_card' in vals:
                like = sum(rec.last_post_ids.mapped("likes"))
                comment = sum(rec.last_post_ids.mapped("comments"))
                share = sum(rec.last_post_ids.mapped("shares"))
                save = sum(rec.last_post_ids.mapped("saves"))

                rec.er = ((like + comment + share + save) / 10) / rec.followers
                rec.cpe = rec.rate_card / ((like + comment + share + save) / 10)
        
        return res