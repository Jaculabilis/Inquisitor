# Standard library imports
import os
import logging
import ast


class Dungeon():
	def __init__(self, path):
		"""
		Serves as an interface between Inquisitor and a folder of
		serialized readable items.
		"""
		self.path = path
		self.log = logging.getLogger("inquisitor.dungeon")

	def load_path(self, path):
		self.log.debug("Loading item from {}".format(path))
		with open(path, 'r', encoding='utf-8') as f:
			item = ast.literal_eval(f.read())
		return item

	def load_item(self, source, itemid):
		item_path = os.path.join(self.path, source, itemid + ".item")
		return self.load_path(item_path)

	def save_item(self, item):
		path = os.path.join(self.path, item['source'], item['id'] + ".item")
		self.log.debug("Saving item {} to {}".format(item['id'], path))
		with open(path, 'w', encoding='utf-8') as f:
			f.write(str(item))

	def update(self, itemsource):
		"""
		Fetches items from the given source, saves new active items,
		and clears out old inactive items.
		"""
		new_items = 0
		self.log.info("Updating source {}".format(itemsource.SOURCE))
		# Check if the source has a folder.
		source_folder = os.path.join(self.path, itemsource.SOURCE)
		source_state = os.path.join(source_folder, "state")
		if not os.path.isdir(source_folder):
			self.log.info("Creating folder {}".format(source_folder))
			os.mkdir(source_folder)
			# Initialize persistent state.
			with open(source_state, 'w') as f:
				f.write("{}")
		# Load source persistent state.
		state = self.load_path(source_state)
		# Any inactive items that no longer show up as new should be
		# removed. Track which items to check for inactivity.
		extant_items_to_check = [
			filename
			for filename in os.listdir(source_folder)
			if filename.endswith(".item")]
		# Get the new items from the source.
		source_items = itemsource.fetch_new(state)
		with open(source_state, 'w', encoding='utf-8') as f:
			f.write(str(state))
		for source_item in source_items:
			file_path = os.path.join(source_folder, source_item['id'] + ".item")
			if os.path.isfile(file_path):
				# Still-new items are exempt from activity checks.
				extant_items_to_check.remove(source_item['id'] + ".item")
				item = self.load_path(file_path)
				if not item['active']:
					# Don't reactivate inactive items.
					continue
			else:
				new_items += 1
			# Add new items and update active ones.
			self.save_item(source_item)
		# Check old items for inactivity.
		for extant_item_filename in extant_items_to_check:
			file_path = os.path.join(source_folder, extant_item_filename)
			item = self.load_path(file_path)
			if not item['active']:
				# Remove old inactive items.
				self.log.info("Deleting {}".format(file_path))
				os.remove(file_path)
		return new_items

	def get_active_items(self):
		source_folders = os.listdir(self.path)
		items = []
		for source_folder_name in source_folders:
			items.extend(self.get_active_items_for_folder(source_folder_name))
		return items

	def get_active_items_for_folder(self, source):
		source_folder = os.path.join(self.path, source)
		item_filenames = os.listdir(source_folder)
		items = []
		for item_filename in item_filenames:
			if not item_filename.endswith(".item"):
				continue
			file_path = os.path.join(source_folder, item_filename)
			item = self.load_path(file_path)
			if item['active']:
				items.append(item)
		return items

	def deactivate_item(self, source, itemid):
		item_path = os.path.join(self.path, source, itemid + ".item")
		if not os.path.isfile(item_path):
			self.log.error("No item found: {}".format(item_path))
			return
		item = self.load_path(item_path)
		item['active'] = False
		self.save_item(item)
		return item
