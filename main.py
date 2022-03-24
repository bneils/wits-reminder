#!/usr/bin/env python3
from scraper import WITSession
from messenger import send_message
from deltas import record_updated_contents, write_records

from urllib.parse import parse_qs
from json import dumps, loads
from os import getenv

def main():
	session = WITSession() 
	session.cookie_authenticate()
	classes = session.fetch_ext_of_classes()
	
	for class_ in classes:
		notes = session.fetch_class_notes(class_)
		grades = session.fetch_class_grades(class_)

		class_id = parse_qs(class_)["class_id"][0]
		# Each line corresponds to a stringified JSON dict of a grade
		# in the marking period, in order.
		grade_lines = [
			dumps(grade, sort_keys=True)
			for mp in range(1, len(grades) + 1)
			for grade in grades[f"mp{mp}"]
		]
		deltas = record_updated_contents(f"{class_id}g", grade_lines)
		# Each line in the text is like:
		# + Unit9 HW10 (U/3)
		# which means, a new grade was added, out of three points, which is to be uploaded later.
		message_body = []
		for delta in deltas:
			grade = loads(delta[2:])
			score = grade.get("Score", "?") if not grade.get("Assignment Upload", "").strip() else "U"
			message_body.append("%s %s %s/%s" % (delta[0], grade.get("Assignment", "Unknown assignment"), score, grade.get("Max Score", "?")))
		
		if message_body:
			send_message(
				"Grades changed",
				"\n\n" + "\n\n".join(message_body),
				getenv("EMAIL_SMS_TO"),
			)

		deltas = record_updated_contents(f"{class_id}n", notes.splitlines())
		# This is similar... except I need to tell them what class it is!
		message_body = []
		for delta in deltas:
			if len(delta.strip()) == 1: # This is just a change in whitespace.
				continue
			message_body.append(f"{delta[0]} {delta[2:]}")
		if message_body:
			send_message(
				"Notes changed",
				"\n\n" + "\n\n".join(message_body),
				getenv("EMAIL_SMS_TO"),
			)

	mail_ids = session.fetch_mail_ids()
	deltas = record_updated_contents(f"mailids", mail_ids)
	
	# Only show *new* mail. Deleted and/or out-of-scope mail should not be reported.
	for delta in deltas:
		if delta[0] != '+':
			continue
	
		mail_id = delta[2:]
		letter = session.fetch_letter(mail_id)
		body = letter["body"]

		send_message(
			"New WITSmail",
			"\n\n" + letter["header"].get("Subject:", "No Subject") + "\n\nFrom: " + letter["header"].get("From:", "Anonymous") + "\n\n" + body[:128] + ("..." if len(body) > 128 else ""),
			getenv("EMAIL_SMS_TO"),
		)

	write_records()

if __name__ == "__main__":
	main()

