from dotenv import load_dotenv

import os
import smtplib
from email.message import EmailMessage

load_dotenv()

def send_message(subject, body, to):
    """Sends a text message using email."""
    message = EmailMessage()
    message.set_content(body)
    message["subject"] = subject
    message["to"] = to
    
    message["from"] = os.getenv("EMAIL_FROM")
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(os.getenv("EMAIL_FROM"), os.getenv("EMAIL_APP_PASS"))
    server.send_message(message)
    server.quit()

    # Messages in the format: / Subject / Body
