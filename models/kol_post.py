import requests
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError

class KolPost(models.Model):
    _name = "kol.post"
    _description = "KOL Post"

    account_id = fields.Many2one('kol.account', string="Account", required=True)
    platform_id = fields.Many2one('kol.platform', string="Platform", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id.id)
    cost = fields.Integer(string="Cost", currency_field="currency_id", required=True)
    post_url = fields.Char(string="Post URL", required=True)
    views = fields.Integer(string="Views")
    likes = fields.Integer(string="Likes")
    comments = fields.Integer(string="Comments")
    shares = fields.Integer(string="Shares")
    saves = fields.Integer(string="Saves")
    cpv = fields.Monetary(string="CPV", help="Cost per View", currency_field="currency_id")
    cpe = fields.Monetary(string="CPE", help="Cost per Engagement", currency_field="currency_id")
    keyword = fields.Char(string="Keyword")
    rpc = fields.Integer(string="RPC", help="Related Product Comments")
    roi = fields.Float(string="ROI", help="Return on Investment")
    description = fields.Text(string="Description")
    post_date = fields.Datetime(string="Post Date")

    @api.model
    def create(self, vals_list):
        record = super(KolPost, self).create(vals_list)
        record.with_delay(
            description=f"Fetch data for {record.account_id.name}"
        )._fetch_apify()
        return record

    def action_refetch_apify(self):
        for rec in self:
            rec._fetch_apify()

    def _fetch_apify(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('apify.api_key')
        if not api_key:
            raise UserError("Apfy API Key is not set. Add it in System Parameters (apify.api_key).")

        if self.platform_id.name == "Tiktok":

            url = f"https://api.apify.com/v2/acts/clockworks~free-tiktok-scraper/run-sync-get-dataset-items?token={api_key}"
            payload = {
                "postURLs": [self.post_url],
                "excludePinnedPosts": True,
                "resultsPerPage": 1,
            }

            resp = requests.post(url, json=payload)
            data = resp.json()

            post = data[0]
            view = post.get("playCount", 0)
            like = post.get("diggCount", 0)
            comment = post.get("commentCount", 0)
            share = post.get("shareCount", 0)
            save = post.get("collectCount", 0)

            post_date = False
            try:
                post_date = datetime.strptime(post.get("createTimeISO").replace("Z", ""), "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    post_date = datetime.strptime(post.get("createTimeIso").replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    post_date = False
            
            self.views = view
            self.likes = like
            self.comments = comment
            self.shares = share
            self.saves = save
            self.cpv = self.cost / view
            self.cpe = self.cost / (like + comment + share + save)
            self.post_date = post_date
            
        return True
