#!/usr/bin/env python3
from scraper import WITSession
from messenger import send_message

def main():
    session = WITSession()
    mail_ids = session.get_mail(1)
    session.get_letter(int(mail_ids[0]))
    #new_mail_ids = session.new_mail()
    #if len(new_mail_ids) <= 5:  # Too many to remind!
       

if __name__ == "__main__":
    main()
