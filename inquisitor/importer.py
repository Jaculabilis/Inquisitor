import os
import traceback
import importlib.util
import json
import sys

from inquisitor import loader, timestamp, error
from inquisitor.configs import SOURCES_PATH, DUNGEON_PATH, logger

def update_sources(*source_names):
	sys.path.append(SOURCES_PATH)
	for source_name in source_names:
		try:
			source_module = load_source(source_name)
		except Exception:
			error.as_item("Error importing source '{}'".format(source_name), traceback.format_exc())
			continue

		cell_path = os.path.join(DUNGEON_PATH, source_name)
		if not os.path.isdir(cell_path):
			try:
				logger.info("Creating cell for source '{}'".format(source_name))
				os.mkdir(cell_path)
				state_path = os.path.join(cell_path, "state")
				with open(state_path, 'w', encoding='utf8') as f:
					f.write(json.dumps({}))
			except Exception:
				error.as_item("Error initializing source '{}'".format(source_name), traceback.format_exc())
				continue

		try:
			logger.info("Updating source '{}'".format(source_name))
			new_count, del_count = update_source(source_name, source_module.fetch_new)
			logger.info("{} new item{}, {} deleted item{}".format(
				new_count, "s" if new_count != 1 else "",
				del_count, "s" if del_count != 1 else ""))
		except Exception:
			error.as_item("Error updating source '{}'".format(source_name), traceback.format_exc())

def load_source(source_name):
	"""
	Attempts to load the source module with the given name. Raises an exception on failure.
	"""
	# Push the sources directory
	cwd = os.getcwd()
	os.chdir(SOURCES_PATH)
	# Check if the named source is present.
	source_file_name = source_name + ".py"
	if not os.path.isfile(source_file_name):
		os.chdir(cwd)
		raise FileNotFoundError("Missing '{}' in '{}'".format(source_name, SOURCES_PATH))
	# Try to import the source module.
	logger.debug("Loading module {}".format(source_file_name))
	spec = importlib.util.spec_from_file_location("itemsource", source_file_name)
	itemsource = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(itemsource)
	if not hasattr(itemsource, 'fetch_new'):
		raise ImportError("Missing fetch_new in '{}'".format(source_file_name))
	# Since the source is valid, get or create the source cell.
	os.chdir(cwd)
	return itemsource

def update_source(source_name, fetch_new):
	"""
	Attempts to update the given source. Raises an exception if the source does.
	"""
	# Get the existing items from the source's cell.
	prior_items, errors = loader.load_items(source_name)
	if any(errors):
		raise Exception(f'Can\'t update source "{source_name}", some items are corrupt')
	logger.debug("Found {} prior items".format(len(prior_items)))

	# Get the feed items from the source's fetch method.
	state = loader.load_state(source_name)
	fetched = fetch_new(state)
	fetched_items = {item['id']: item for item in fetched}
	state.flush()

	# Populate all the fetched items with required or auto-generated fields.
	# This also provides an opportunity to throw if the source isn't returning
	# valid items.
	for item in fetched_items.values():
		populate_new(source_name, item)
	logger.debug("Fetched {} items".format(len(fetched_items)))

	# Write all the new fetched items to the source's cell.
	new_items = [
		item for item in fetched_items.values()
		if item['id'] not in prior_items]
	for item in new_items:
		s = json.dumps(item)
		path = os.path.join(DUNGEON_PATH, item['source'], item['id'] + ".item")
		with open(path, 'w', encoding='utf8') as f:
			f.write(s)

	# Update the extant items using the fetched item's values.
	extant_items = [
		item for item in fetched_items.values()
		if item['id'] in prior_items]
	for item in extant_items:
		# The items in prior_items are writethrough dicts.
		prior_item = prior_items[item['id']]
		# Only bother updating active items.
		if prior_item['active']:
			populate_old(prior_item, item)

	# In general, items are removed when they are old (not found in the last
	# fetch) and inactive. Some item fields can change this basic behavior.
	del_count = 0
	now = timestamp.now()
	old_items = [
		item for item in prior_items.values()
		if item['id'] not in fetched_items]
	for item in old_items:
		remove = not item['active']
		# The time-to-live field protects an item from removal until expiry.
		# This is mainly used to avoid old items resurfacing when their source
		# cannot guarantee monotonicity.
		if 'ttl' in item:
			ttl_date = item['created'] + item['ttl']
			if ttl_date > now:
				continue
		# The time-to-die field can force an active item to be removed.
		if 'ttd' in item:
			ttd_date = item['created'] + item['ttd']
			if ttd_date < now:
				remove = True
		# Items to be removed are deleted
		if remove:
			del_count += 1
			file_path = os.path.join(DUNGEON_PATH, item['source'], item['id'] + ".item")
			try:
				os.remove(file_path)
			except:
				error.as_item("Failed to delete {}".format(file_path))

	# Note update timestamp in state
	state['last_updated'] = timestamp.now()

	# Return counts
	return len(new_items), del_count

def populate_new(source_name, item):
	# id is required
	if 'id' not in item:
		raise Exception(f'Source "{source_name}" returned an item with no id')
	# source is auto-populated with the source name if missing
	if 'source' not in item: item['source'] = source_name
	# active is forced to True for new items
	item['active'] = True
	# created is forced to the current timestamp
	item['created'] = timestamp.now()
	# title is auto-populated with the id if missing
	if 'title' not in item: item['title'] = item['id']
	# tags is auto-populated if missing (not if empty!)
	if 'tags' not in item: item['tags'] = [source_name]
	# link, time, author, body, ttl, ttd, and tts are optional

def populate_old(prior, new):
	# Not updated: id, source, active, created
	if 'title' in new: prior['title'] = new['title']
	if 'tags' in new: prior['tags'] = new['tags']
	if 'link' in new: prior['link'] = new['link']
	if 'time' in new: prior['time'] = new['time']
	if 'author' in new: prior['author'] = new['author']
	if 'body' in new: prior['body'] = new['body']
	if 'ttl' in new: prior['ttl'] = new['ttl']
	if 'ttd' in new: prior['ttd'] = new['ttd']
	if 'tts' in new: prior['tts'] = new['tts']
