#!/usr/bin/env python3
from scraper import WITSession, print_letter
from messenger import send_message

def main():
	session = WITSession() 
	session.cookie_authenticate()

if __name__ == "__main__":
	main()
