from difflib import ndiff
import json
from pathlib import Path

# This module records information it receives, and retrieves old information.
# It also returns the deltas of lines it sees

# storage.json is loaded, modified a lot, and then saved.

path = Path(__file__)

try:
	with path.with_name("storage.json").open("r") as f:
		_class_information = json.load(f)
except json.JSONDecodeError:
	_class_information = {}
except FileNotFoundError:
	_class_information = {}
	with path.with_name("storage.json").open("w") as f:
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

def write_records():
	with path.with_name("storage.json").open("w") as f:
		json.dump(_class_information, f)
