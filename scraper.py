import os
from math import ceil
from urllib.parse import urlparse, parse_qs
import json
from pathlib import Path
from typing import List, Dict, Any

import requests
import bs4
from bs4 import BeautifulSoup, SoupStrainer
from dotenv import load_dotenv, find_dotenv

path = Path(__file__)

# Constants, environs
load_dotenv(find_dotenv())

NON_BREAKING_SPACE = "\xa0"

def _recursively_unfold_content(el):
	contents = []
	for child in el.contents:
		if isinstance(child, str):
			contents.append(child.replace(NON_BREAKING_SPACE, " ").strip())
		else:
			contents.extend(_recursively_unfold_content(child))
	return contents


class AuthenticationError(Exception):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class WITS:
	URL = "https://wits.williamsvillek12.org"
	HOME = URL + "/data/WITS"
	AUTH = URL + "/data/AuthenticateLogin"
	MAIL = URL + "/data/WITSMail?folder=inbox&page=%d"
	CLASSES = URL + "/data/ViewStudentClasses"
	ASSIGNMENTS = URL + "/data/ClassAssignments"   
	CLASS = URL + "/ViewClassNotes?teacher_id=%s&class_id=%s"
	MESSAGE = URL + "/data/ViewMessage?folder=inbox&wits_mail_id=%s"


class WITSession(requests.Session):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def authenticate(self, load_homepage: bool = True):
		"""Authenticates the session using SCHOOL_USER and SCHOOL_PASS environ variables"""
		data = {
			"username": os.getenv("SCHOOL_USER"),
			"password": os.getenv("SCHOOL_PASS"),
		}
		resp = self.post(WITS.AUTH, data=data)
		if not resp.json()["data"]["authenticated"]:	 
			raise AuthenticationError("Credentials not correct, or server-side issue")
		
		self._save_cookies()

		# If this GET is not made, then the next GET is made here anyways.
		if load_homepage:
			self.get(WITS.HOME)

	def _save_cookies(self, fp: str = "cookies.json"):
		"""Saves the current session's cookies inside a JSON file"""
		with path.with_name(fp).open("w") as f:
			json.dump(self.cookies.get_dict(), f)

	def _load_cookies(self, fp: str = "cookies.json"):
		"""Loads the current session's cookies from a cookie file."""
		with path.with_name(fp).open("r") as f:
			self.cookies = requests.cookies.cookiejar_from_dict(json.load(f))

	def cookie_authenticate(self):
		"""Preferred way of authentication, will try to use a cookie in-place."""
		try:
			self._load_cookies()
			resp = self.get(WITS.HOME)
			for script_tag in BeautifulSoup(resp.content, features="html.parser", parse_only=SoupStrainer("script")):
				if "login" in script_tag.get("src", ""):
					self.authenticate()
					break
		except FileNotFoundError:
			self.authenticate()
	
	def fetch_mail_ids(self, num: int = 100) -> List[str]:
		"""Obtain most recent mail ids from WITSmail"""
		if num <= 0:
			return []

		mail_ids = []
		for page in range(1, ceil(num / 100) + 1):
			resp = self.get(WITS.MAIL % page)
			# This parses the WITSmail page, then iterates through all links, filters the non-mail links, and gets the ID from each link.
			for link in BeautifulSoup(resp.content, features="html.parser", parse_only=SoupStrainer("a")):
				if link.get("href", "").startswith("ViewMessage"):
					queries = parse_qs(urlparse(link["href"]).query)
					mail_ids.append(queries["wits_mail_id"][0])
					num -= 1
					if num == 0:
						break
		return mail_ids

	def fetch_letter(self, mail_id: str) -> Dict[str, Any]:
		"""Get a specific letter from your inbox.
		Returns a dict like:
		"header":
			"Received:":str,
			"From:":str,
			"To:":str,
			"Subject:":str,
		"body": str,
		"""
	
		# Letter contents inside <div class="col-xs-12 col-sm-9 col-lg-10"></div>:
		resp = self.get(WITS.MESSAGE % mail_id)
		soup = BeautifulSoup(resp.content, "html.parser")
		message = {}
	
		# Get the letter's metadata.
		message["header"] = {
			key.string: value.string for key, value in zip(
			  soup.find_all("label", class_="col-sm-2 control-label"),
			  soup.find_all("div", class_="col-sm-10 form-control-static")
			)
		}
		# Find all <p> in this div and recursively unfold it, removing ascii A0
		message["body"] = "\n".join(
			"".join(_recursively_unfold_content(p)) for p in soup.find("div", class_="col-xs-12 col-sm-9 col-lg-10").find_all("p")
		)

		return message

	def fetch_ext_of_classes(self) -> List[str]:
		"""Obtain a list of the current classes."""
		resp = self.get(WITS.CLASSES)
		
		classes = [
			link["href"] for link in BeautifulSoup(resp.content, features="html.parser", parse_only=SoupStrainer("a"))
			if link.get("href", "").startswith("ViewClassNotes")
		]
		return classes

	def fetch_class_notes(self, class_url_ext: str) -> str:
		"""Obtain the notes for a class given its url extension (e.g. ViewClassNotes?teacher_id=3210)"""
		resp = self.get(WITS.URL + "/data/" + class_url_ext)
		soup = BeautifulSoup(resp.content, "html.parser")
		lines = []
		box_element = soup.find(id="content-bounding-box")
		if box_element is None:
			return ""
		for ptag in box_element.find_all("p"):
			lines.append(" ".join(_recursively_unfold_content(ptag)))
		return "\n".join(lines)
	
	def fetch_class_grades(self, class_url_ext: str) -> str:
		"""
		Obtain a list of grades
		Returns dict with keys: mp1, mp2, etc.
		Those keys have a list of grades, represented as dicts with keys:
		Assignment, Assignment Upload, Category, Date, Max Score, Scale, Score
		"""
		args = parse_qs(class_url_ext)
		resp = self.get(WITS.URL + "/data/" + class_url_ext + "&tab=grades")
		soup = BeautifulSoup(resp.content, "html.parser")
		grades = {}
		for mp in range(1, 5):
			marking_period_grades = []
			# Get the table for the marking period.
			mp_tag = soup.find("div", id=f"mp-{args['class_id'][0]}-{mp}")
			if not mp_tag:
				break

			for tag in mp_tag:
				# Not all of the tags are of Tag, some are NavigableString
				if isinstance(tag, bs4.element.Tag):
					rows = tag.find_all("tr")
					col_names = [col.text.replace(NON_BREAKING_SPACE, " ") for col in rows[0].find_all("td")]
					for row in rows[1:]:
						columns = [col.text.replace(NON_BREAKING_SPACE, " ") for col in row.find_all("td")]
						grade = {name:col for name, col in zip(col_names, columns)}
						marking_period_grades.append(grade)
			grades[f"mp{mp}"] = marking_period_grades

		return grades
