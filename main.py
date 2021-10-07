#!/usr/bin/env python3
from scraper import WITSession
from messenger import send_message

def main():
    session = WITSession() 
    print(session.get_letter(session.get_mail(1).pop())["body"])

if __name__ == "__main__":
    main()
