import os
from math import ceil
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup, SoupStrainer
from dotenv import load_dotenv

# Constants, environs
load_dotenv()

class WITSession(requests.Session):
    URL = "https://wits.williamsvillek12.org"
    HOME = URL + "/data/WITS"
    AUTH = URL + "/data/AuthenticateLogin"
    MAIL = URL + "/data/WITSMail?folder=inbox&page=%d"
    CLASSES = URL + "/data/ViewStudentClasses"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._authenticate()

    def _authenticate(self):
        """Authenticates the session using SCHOOL_USER, SCHOOL_PASS"""
        data = {
            "username": os.getenv("SCHOOL_USER"),
            "password": os.getenv("SCHOOL_PASS"),
        }
        resp = self.post(WITSession.AUTH, data=data)
        if not resp.json().get("data", {}).get("authenticated"):
            raise ValueError("Credentials are not correct (or WITS isn't serving?)")
        
        # I don't know why this needs to be done, but if it isn't, any subsequent GETs will redirect here anyways. wtf WITS?
        self.get(WITSession.HOME)

    def get_mail(self, num=100):
        """Obtain mail ids in WITSmail"""
        mail_ids = []

        assert num > 0, "must get some mail"

        for page in range(1, ceil(num / 100) + 1):
            resp = self.get(WITSession.MAIL % page)
            # This parses the WITSmail page, then iterates through all links, filters the non-mail links, and gets the ID from each link.
            for link in BeautifulSoup(resp.content, features="html.parser", parse_only=SoupStrainer("a")):
                if link.has_attr("href") and link["href"].startswith("ViewMessage"):
                    queries = parse_qs(urlparse(link["href"]).query)
                    mail_ids.append(queries["wits_mail_id"][0])
                    num -= 1
                    if num == 0:
                        break
        return mail

    def new_mail(self):
        """Get new WITSmail, since last checked"""
        mail = self.get_mail()

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

    def get_classes(self):
        """Obtain a list of the current classes."""
        resp = self.get(WITSession.CLASSES)
            
        classes = [
            link["href"] for link in BeautifulSoup(resp.content, features="html.parser", parse_only=SoupStrainer("a"))
            if link.has_attr("href") and link["href"].startswith("ViewClassNotes")
        ]
        return classes

    def get_notes(self, class_):
        """Obtain a list of the notes for a class"""
         
# TODO: SAVE TOKEN AND CHECK IF STALE (same as storing credentials in untracked file, but skips auth)
# TODO: ADD OPTION TO RUN WITHOUT SENDING ANYTHING (or if it exceeds a point, just tell them how many they received)

if __name__ == "__main__":
    session = WITSession()
