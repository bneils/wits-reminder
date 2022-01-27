from difflib import ndiff
import json
import atexit

# This module records information it receives, and retrieves old information.
# It also returns the deltas of lines it sees

# storage.json is loaded, modified a lot, and then saved.

try:
	with open("storage.json") as f:
		_class_information = json.load(f)
except json.JSONDecodeError:
	_class_information = {}
except FileNotFoundError:
	_class_information = {}
	with open("storage.json", "w") as f:
		f.write("{}")


def record_updated_contents(name, lines):
	"""Enters the name:lines into the dict and returns the deltas"""
	if name in _class_information:
		prev_lines = _class_information[name]
		deltas = [diff for diff in ndiff(prev_lines, lines) if diff[0] in "-+"]
	else:
		deltas = []
	_class_information[name] = lines
	return deltas

def _write_records():
	with open("storage.json", "w") as f:
		json.dump(_class_information, f)

if __name__ != "__main__":
	atexit.register(_write_records)