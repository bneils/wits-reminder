import os
from math import ceil
from urllib.parse import urlparse, parse_qs
import json

import requests
from bs4 import BeautifulSoup, SoupStrainer
from dotenv import load_dotenv

# Constants, environs
load_dotenv()


class AuthenticationError(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class WITSession(requests.Session):
    URL = "https://wits.williamsvillek12.org"
    HOME = URL + "/data/WITS"
    AUTH = URL + "/data/AuthenticateLogin"
    MAIL = URL + "/data/WITSMail?folder=inbox&page=%d"
    CLASSES = URL + "/data/ViewStudentClasses"
    ASSIGNMENTS = URL + "/data/ClassAssignments"   
    MESSAGE = URL + "/data/ViewMessage?folder=inbox&wits_mail_id=%s"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cookie_authenticate()

    def authenticate(self, load_homepage=True):
        """Authenticates the session using SCHOOL_USER and SCHOOL_PASS environ variables"""
        data = {
            "username": os.getenv("SCHOOL_USER"),
            "password": os.getenv("SCHOOL_PASS"),
        }
        resp = self.post(WITSession.AUTH, data=data)
        if not resp.json()["data"]["authenticated"]:     
            raise AuthenticationError("Credentials not correct, or serverside issue")
        
        self._save_cookies()

        # If this GET is not made, then the next GET is made here anyways.
        if load_homepage:
            self.get(WITSession.HOME)

    def _save_cookies(self, fp="cookies.json"):
        """Saves the current session's cookies inside a pickle file."""
        with open(fp, "w") as f:
            json.dump(self.cookies.get_dict(), f)

    def _load_cookies(self, fp="cookies.json"):
        """Loads the current session's cookies from a cookie file."""
        with open(fp) as f:
            self.cookies = requests.cookies.cookiejar_from_dict(json.load(f))

    def cookie_authenticate(self):
        """Preferred way of authentication, will try to use a cookie in-place."""
        try:
            self._load_cookies()
            resp = self.get(WITSession.HOME)
            for script_tag in BeautifulSoup(resp.content, features="html.parser", parse_only=SoupStrainer("script")):
                if "login" in script_tag.get("src", ""):
                    self.authenticate()
                    break
        except FileNotFoundError:
            self.authenticate()
    
    def get_mail(self, num=100):
        """Obtain most recent mail ids from WITSmail"""
        mail_ids = []

        assert num > 0, "must get some mail"

        for page in range(1, ceil(num / 100) + 1):
            resp = self.get(WITSession.MAIL % page)
            # This parses the WITSmail page, then iterates through all links, filters the non-mail links, and gets the ID from each link.
            for link in BeautifulSoup(resp.content, features="html.parser", parse_only=SoupStrainer("a")):
                if link.get("href", "").startswith("ViewMessage"):
                    queries = parse_qs(urlparse(link["href"]).query)
                    mail_ids.append(queries["wits_mail_id"][0])
                    num -= 1
                    if num == 0:
                        break
        return mail_ids

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

        return set(mail) - set(last_read_mail)

    def get_letter(self, mail_id):
        """Get a specific letter from your inbox."""
   
        def _recursive_content(item):
            contents = []
            for i in item.contents:
                if isinstance(i, str):
                    contents.append(i.replace("\xa0", " "))
                else:
                    contents.extend(_recursive_content(i))
            return contents
 
        # Letter contents inside <div class="col-xs-12 col-sm-9 col-lg-10"></div>:
        resp = self.get(WITSession.MESSAGE % mail_id)
        soup = BeautifulSoup(resp.content, "html.parser")
        message = {}
    
        # Get the letter's metadata.
        message["header"] = {
            key.string: value.string for key, value in zip(
              soup.find_all("label", class_="col-sm-2 control-label"),
              soup.find_all("div", class_="col-sm-10 form-control-static")
            )
        }
        message["body"] = "\n".join(
            "".join(_recursive_content(p)) for p in soup.find("div", class_="col-xs-12 col-sm-9 col-lg-10").find_all("p")
        )

        return message

    def get_classes(self):
        """Obtain a list of the current classes."""
        resp = self.get(WITSession.CLASSES)
         
        classes = [
            link["href"] for link in BeautifulSoup(resp.content, features="html.parser", parse_only=SoupStrainer("a"))
            if link.get("href", "").startswith("ViewClassNotes")
        ]
        return classes

    def get_notes(self, class_):
        """Obtain a list of the notes for a class"""
        raise NotImplementedError()

    def get_quarterly_grades(self):
        """Obtain a list of grades for each class"""
        #resp = self.get(WITSession.ASSIGNMENTS)
        raise NotImplementedError()

