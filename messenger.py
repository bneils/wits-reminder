import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

def send_message(subject: str, body: str, to: str):
	"""Sends a text message using email.
	Messages in the format: / Subject / Body
	Subject has a character limit (probably).
	To create a divide use two newlines.
	"""

	message = EmailMessage()
	message.set_content(body)
	message["Subject"] = subject
	message["To"] = to
	
	message["From"] = os.getenv("EMAIL_FROM")
	server = smtplib.SMTP("smtp.gmail.com", 587)
	server.starttls()
	server.login(os.getenv("EMAIL_FROM"), os.getenv("EMAIL_APP_PASS"))
	server.send_message(message)
	server.quit()