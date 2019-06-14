# Standard library imports
import os
import logging
import ast
import importlib.util
import time
import random
import traceback


# Application imports
from item import create_item


# Globals
logger = logging.getLogger("inquisitor.dungeon")


class ReadableItem():
	"""
	An abstraction layer around items saved in dungeon cell folders.
	Provides read-only access with a deactivation function.
	If the underlying item is changed, those changes may be overwritten by deactivation.

	Members:
	path: path to the wrapped item's file
	cell: name of the cell the item is in
	id: the item's id
	item: the wrapped item
	"""
	def __init__(self, dungeon_path, cell_name, item_id):
		self.path = os.path.join(dungeon_path, cell_name, item_id + ".item")
		self.cell = cell_name
		self.id = item_id
		logger.debug("Loading '{0.id}' from '{0.cell}'".format(self))
		with open(self.path, 'r', encoding='utf-8') as f:
			self.item = ast.literal_eval(f.read())

	def __getitem__(self, key):
		return self.item[key]

	def __setitem__(self, key, value):
		raise TypeError("ReadableItem is not writable")

	def __contains__(self, key):
		return key in self.item

	def __repr__(self):
		return "ReadableItem({0.cell}/{0.id})".format(self)

	def __str__(self):
		return repr(self)

	def deactivate(self):
		self.item['active'] = False
		logger.debug("Deactivating item at {0.path}".format(self))
		with open(self.path, 'w', encoding='utf-8') as f:
			f.write(str(self.item))


class DungeonCell():
	"""
	An abstraction layer around a folder containing items generated by an item source.

	Members:
	name: the cell's source's name
	dungeon_path: the path to the dungeon containing this cell
	path: the path to this cell
	state: the source's persistent state dictionary
	"""
	def __init__(self, dungeon_path, name):
		self.name = name
		self.dungeon_path = dungeon_path
		self.path = os.path.join(dungeon_path, name)
		state_path = os.path.join(self.path, "state")
		if not os.path.isdir(self.path):
			# Initialize cell state on the disk.
			logger.info("Creating folder for cell {}".format(name))
			os.mkdir(self.path)
			self.state = {}
			with open(state_path, 'w', encoding='utf-8') as f:
				f.write(str(self.state))
		else:
			# Load cell state from the disk.
			with open(state_path, 'r', encoding='utf-8') as f:
				self.state = ast.literal_eval(f.read())

	def _item_path(key):
		return os.path.join(self.path, key + ".item")

	def __getitem__(self, key):
		filepath = self._item_path(key)
		if not os.path.isfile(filepath):
			raise KeyError("No item '{}' in cell '{}'".format(key, self.name))
		return ReadableItem(self.dungeon_path, self.name, key)

	def __setitem__(self, key, value):
		logger.info("Setting item {} in cell {}".format(key, self.name))
		if type(value) is ReadableItem:
			value = value.item
		if type(value) is not dict:
			raise TypeError("Can't store a '{}' as '{}': not a dict".format(type(value), key))
		filepath = self._item_path(key)
		with open(filepath, 'w', encoding='utf-8') as f:
			f.write(str(value))

	def __delitem__(self, key):
		logger.info("Deleting item '{}' in cell '{}'".format(key, self.name))
		filepath = self._item_path(key)
		if os.path.isfile(filepath):
			os.remove(filepath)

	def __contains__(self, key):
		for item in self:
			if item == key:
				return True
		return False

	def __iter__(self):
		for filename in os.listdir(self.path):
			if filename.endswith(".item"):
				yield filename[:-5]

	def save_state(self):
		filepath = os.path.join(self.path, 'state')
		with open(filepath, 'w', encoding='utf-8') as f:
			f.write(str(self.state))

	def update_from_source(self, source, args):
		logger.info("Updating source {}".format(self.name))
		# Get the ids of the existing items.
		prior_item_ids = [item_id for item_id in self]
		# Get the new items.
		new_items = itemsource.fetch_new(state, args)
		self.save_state()
		new_count = del_count = 0
		for item in new_items:
			# Store new items unconditionally.
			if item['id'] not in prior_item_ids:
				new_count += 1
				self[item['id']] = item
			# Update extant items if active, otherwise inactive items will be
			# reactivated by the overwrite.
			else:
				prior_item = self[item['id']]
				if prior_item['active']:
					self[item['id']] = item
				# Remove the id from the list to track its continued presence
				# in the source's queue of new items.
				prior_item_ids.remove(item['id'])
		# Any extant item left in the list is old. Remove any items that are
		# both old and inactive.
		for prior_id in prior_item_ids:
			if not self[prior_id]['active']:
				del_count += 1
				del self[prior_id]
		# Return counts
		return new_count, del_count


class Dungeon():
	"""
	A wrapper for dealing with a collection of DungeonCell folders.
	Interfaces between Inquisitor and the ReadableItems produced by its
	sources.
	"""
	def __init__(self, path):
		self.path = path
		# Initialize DungeonCells for each folder with a state file
		self.cells = {}
		for filename in os.listdir(self.path):
			if not os.path.isdir(os.path.join(self.path, filename)):
				continue
			if not os.path.isfile(os.path.join(self.path, filename, 'status')):
				continue
			self.cells[filename] = DungeonCell(self.path, filename)
		# Ensure Inquisitor's source is present
		if "inquisitor" not in self.cells:
			self.cells["inquisitor"] = DungeonCell(self.path, 'inquisitor')

	def __getitem__(self, key):
		return self.cells[key]

	def __setitem__(self, key, value):
		if type(value) is not DungeonCell:
			raise TypeError("Can't store a '{}' as '{}': not a DungeonCell".format(type(value), key))
		self.cells[key] = value

	def __contains__(self, key):
		return key in self.cells

	def __iter__(self):
		for name in self.cells:
			yield name

	def push_error_item(self, title, body=None):
		logger.error(title)
		item = create_item(
			'inquisitor',
			'{:x}'.format(random.getrandbits(16 * 4)),
			title,
			body="<pre>{}</pre>".format(body) if body else None)
		self['inquisitor'][item['id']] = item

	def try_load_source(self, sources_path, source_name):
		"""
		Tries to load the given source, creating a cell in the dungeon if
		necessary. Returns the source and its DungeonCell if the source is
		valid and None, None otherwise.
		"""
		# Check if the named source is present in the sources directory.
		source_file_path = os.path.join(sources_path, source_name + ".py")
		if not os.path.isfile(source_file_path):
			msg = "Could not find source '{}'".format(source_name)
			self.push_error_item(msg)
			return None, None
		# Try to import the source module.
		try:
			logger.debug("Loading module {}".format(source_file_path))
			spec = importlib.util.spec_from_file_location("itemsource", source_file_path)
			itemsource = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(itemsource)
			if not hasattr(itemsource, 'fetch_new'):
				raise ImportError("fetch_new missing")
		except Exception:
			msg = "Error importing source '{}'".format(source_name)
			self.push_error_item(msg, traceback.format_exc())
			return None, None
		# Since the source is valid, get or create the source cell.
		if source_name not in self:
			self[source_name] = DungeonCell(self.path, source_name)

		return itemsource, self[source_name]

	def update(self, source_arg, args):
		"""
		Loads the given source and fetches new items. Clears old and inactive items.
		"""
		# Split off the source name from the fetch argument.
		splits = source_arg.split(":", maxsplit=1)
		source_name = splits[0]
		source_args = splits[1] if len(splits) > 1 else None

		# Load the source.
		source, cell = self.try_load_source(args.srcdir, source_name)
		if source is None or cell is None:
			# try_load_source has already logged the error
			return

		# Update the cell from the source.
		try:
			new_count, deleted_count = cell.update_from_source(source, source_args)
			logger.info("{} new item{}, {} deleted item{}".format(
				new_count, "s" if new_count != 1 else "",
				deleted_count, "s" if deleted_count != 1 else ""))
		except:
			msg = "Error fetching items from source '{}'".format(source_name)
			self.push_error_item(msg, traceback.format_exc())
			return
