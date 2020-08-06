import os
import json


from inquisitor.configs import DUNGEON_PATH
from inquisitor import error
from inquisitor import timestamp


class WritethroughDict():
	"""A wrapper for a dictionary saved to the file system."""

	@staticmethod
	def create(path, item):
		"""
		Creates a writethrough dictionary from a dictionary in memory and
		initializes a file to save it.
		"""
		if os.path.isfile(path):
			raise FileExistsError(path)
		wd = WritethroughDict(path, item)
		wd.flush()
		return wd

	@staticmethod
	def load(path):
		"""
		Creates a writethrough dictionary from an existing file in the
		file system.
		"""
		if not os.path.isfile(path):
			raise FileNotFoundError(path)
		with open(path) as f:
			item = json.load(f)
		return WritethroughDict(path, item)

	def __init__(self, path, item):
		self.path = path
		self.item = item

	def __getitem__(self, key):
		return self.item[key]

	def __setitem__(self, key, value):
		self.item[key] = value
		self.flush()

	def set(self, dict):
		for key, value in dict.items():
			self.item[key] = value
		self.flush()

	def __contains__(self, key):
		return key in self.item

	def __repr__(self):
		return repr(self.item)

	def __str__(self):
		return str(self.item)

	def flush(self):
		s = json.dumps(self.item, indent=2)
		with open(self.path, 'w', encoding="utf8") as f:
			f.write(s)


def load_state(source_name):
	"""Loads the state dictionary for a source."""
	state_path = os.path.join(DUNGEON_PATH, source_name, "state")
	return WritethroughDict.load(state_path)


def load_item(source_name, item_id):
	"""Loads an item from a source."""
	item_path = os.path.join(DUNGEON_PATH, source_name, f'{item_id}.item')
	return WritethroughDict.load(item_path)

def load_items(source_name):
	"""
	Returns a map of ids to items and a list of unreadable files.
	"""
	cell_path = os.path.join(DUNGEON_PATH, source_name)
	items = {}
	errors = []
	for filename in os.listdir(cell_path):
		if filename.endswith('.item'):
			try:
				item = load_item(source_name, filename[:-5])
				items[item['id']] = item
			except Exception:
				errors.append(filename)
	return items, errors

def load_active_items():
	"""
	Returns a list of active items and a list of unreadable items.
	"""
	items = []
	errors = []
	now = timestamp.now()
	for cell_name in os.listdir(DUNGEON_PATH):
		cell_path = os.path.join(DUNGEON_PATH, cell_name)
		for filename in os.listdir(cell_path):
			if filename.endswith('.item'):
				try:
					item = load_item(cell_name, filename[:-5])
					# The time-to-show field hides items until an expiry date.
					if 'tts' in item:
						tts_date = item['created'] + item['tts']
						if now < tts_date:
							continue
					# Don't show inactive items
					if not item['active']:
						continue
					items.append(item)
				except Exception:
					errors.append(filename)
	return items, errors
