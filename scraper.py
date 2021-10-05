import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup, SoupStrainer

import os
from urllib.parse import urlparse, parse_qs

# Constants, environs
load_dotenv()

class Urls:
    URL = "https://wits.williamsvillek12.org"
    AUTH = URL + "/data/AuthenticateLogin"
    MAIL = URL + "/data/WITSMail"

class WITSession(requests.Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._authenticate()

    def _authenticate(self):
        """Authenticates the session using USER_FIELD, PASS_FIELD"""
        data = {
            "username": os.getenv("USER_FIELD"),
            "password": os.getenv("PASS_FIELD"),
        }
        resp = self.post(Urls.AUTH, data=data)
        if not resp.json().get("data", {}).get("authenticated"):
            raise ValueError("Credentials are not correct (or WITS isn't serving?)")

    def new_mail(self):
        """Checks WITSmail for new mail since it checked. authenticate() needs to be called before this"""
        # for some reason, I have to call this twice to get actual results (best to know why or keep trying until it parses)
        self.get(Urls.MAIL)
        resp = self.get(Urls.MAIL)

        # This parses the WITSmail page, then iterates through all links, filters the non-mail links, and gets the ID from each link.
        mail = [
            parse_qs(urlparse(link["href"]).query)["wits_mail_id"][0] for link in BeautifulSoup(resp.content, features="html.parser", parse_only=SoupStrainer("a"))
            if link.has_attr("href") and link["href"].startswith("ViewMessage")
        ]
        
        # Get last scan
        try:
            with open("mail_ids.txt") as f:
                last_read_mail = f.read().splitlines()
        except FileNotFoundError:
            last_read_mail = []
        
        # Update
        with open("mail_ids.txt", "w") as f:
            f.write("\n".join(mail))

        difference = set(mail) - set(last_read_mail)
        return difference
         
# TODO: SAVE TOKEN AND CHECK IF STALE (same as storing credentials, but skips auth)
# TODO: ADD OPTION TO RUN WITHOUT SENDING ANYTHING (or if it exceeds a point, just tell them how many they received)

