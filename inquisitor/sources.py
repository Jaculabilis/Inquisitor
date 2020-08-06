import os
import traceback
import importlib.util
import json
import sys


from inquisitor import loader, timestamp, error
from inquisitor.configs import SOURCES_PATH, DUNGEON_PATH, logger


def ensure_cell(name):
	"""
	Creates a cell in the dungeon. Idempotent.
	"""
	cell_path = os.path.join(DUNGEON_PATH, name)
	if not os.path.isdir(cell_path):
		logger.info(f'Creating cell for source "{name}"')
		os.mkdir(cell_path)
	state_path = os.path.join(cell_path, 'state')
	if not os.path.isfile(state_path):
		with open(state_path, 'w', encoding='utf8') as state:
			json.dump({}, state)


def update_sources(*source_names):
	"""
	Attempts to update each given source.
	"""
	for source_name in source_names:
		# Import the source
		try:
			source_module = load_source(source_name)
		except Exception:
			error.as_item(
				f'Error importing source "{source_name}"',
				traceback.format_exc())
			continue

		# If it doesn't have a cell yet, create one
		try:
			ensure_cell(source_name)
		except Exception:
			error.as_item(
				f'Error initializing source "{source_name}"',
				traceback.format_exc())
			continue

		# Update the source
		try:
			logger.info(f'Updating source "{source_name}"')
			update_source(source_name, source_module.fetch_new)
		except Exception:
			error.as_item(
				f'Error updating source "{source_name}"',
				traceback.format_exc())


def load_source(source_name):
	"""
	Attempts to load the source module with the given name.
	Raises an exception on failure.
	"""
	# Push the sources directory.
	cwd = os.getcwd()
	try:
		os.chdir(SOURCES_PATH)

		# Check if the named source is present.
		source_file_name = source_name + '.py'
		if not os.path.isfile(source_file_name):
			raise FileNotFoundError('Missing "{source_name}" in "{SOURCES_PATH}"')

		# Import the source module by file path.
		logger.debug('Loading module "{source_file_name}"')
		spec = importlib.util.spec_from_file_location("itemsource", source_file_name)
		itemsource = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(itemsource)
		itemsource = importlib.import_module(source_name)

		# Require fetch_new().
		if not hasattr(itemsource, 'fetch_new'):
			raise ImportError('Missing fetch_new in "{source_file_name}"')

		return itemsource

	finally:
		os.chdir(cwd)


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

	# Log counts
	logger.info("{} new item{}, {} deleted item{}".format(
		len(new_items), "s" if len(new_items) != 1 else "",
		del_count, "s" if del_count != 1 else ""))

def populate_new(source_name, item):
	# id is required
	if 'id' not in item:
		raise Exception(f'Source "{source_name}" returned an item with no id')
	# source is auto-populated with the source name if missing
	# Note: this allows sources to create items in other cells!
	if 'source' not in item: item['source'] = source_name
	# active is forced to True for new items
	item['active'] = True
	# created is forced to the current timestamp
	item['created'] = timestamp.now()
	# title is auto-populated with the id if missing
	if 'title' not in item: item['title'] = item['id']
	# tags is auto-populated if missing (not if empty!)
	if 'tags' not in item: item['tags'] = [source_name]
	# link, time, author, body, ttl, ttd, tts, callback are optional

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
	if 'callback' in new: prior['callback'] = new['callback']

def item_callback(source_name, itemid):
	try:
		# Load the module with the callback function
		source_module = load_source(source_name)
		if not hasattr(source_module, 'callback'):
			raise ImportError(f"Missing callback in '{source_name}'")
		# Load the source state and the origin item
		state = loader.load_state(source_name)
		item = loader.WritethroughDict(os.path.join(DUNGEON_PATH, source_name, itemid + ".item"))
		# Execute callback
		source_module.callback(state, item)
		# Save any changes
		item.flush()
		state.flush()
	except Exception:
		error.as_item(f"Error executing callback for {source_name}/{itemid}", traceback.format_exc())
