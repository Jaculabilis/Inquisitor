import os
import traceback
import importlib.util
import json

import error
from configs import SOURCES_PATH, DUNGEON_PATH, logger
import loader
import timestamp

def update_sources(*source_names):
	for source_name in source_names:
		try:
			source_module = load_source(source_name)
		except Exception as e:
			error.as_item("Error importing source '{}'".format(source_name), traceback.format_exc())
			continue

		try:
			logger.info("Updating source '{}'".format(source_name))
			new_count, del_count = update_source(source_name, source_module.fetch_new)
			logger.info("{} new item{}, {} deleted item{}".format(
				new_count, "s" if new_count != 1 else "",
				del_count, "s" if del_count != 1 else ""))
		except Exception as e:
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
	cell_path = os.path.join(DUNGEON_PATH, source_name)
	return itemsource

def update_source(source_name, fetch_new):
	"""
	Attempts to update the given source. Raises an exception if the source does.
	"""
	cell_path  = os.path.join(DUNGEON_PATH, source_name)

	# Get the existing items.
	prior_items, errors = loader.load_items(source_name)
	logger.debug("Found {} prior items".format(len(prior_items)))

	# Get the new items.
	state = loader.load_state(source_name)
	new_items = fetch_new(state)
	logger.debug("Fetched {} items".format(len(new_items)))
	state.flush()

	new_count = 0
	del_count = 0
	for item in new_items:
		populate_new(item)

		if item['id'] not in prior_items:
			# If the item is new, write it.
			new_count += 1
			s = json.dumps(item)
			path = os.path.join(DUNGEON_PATH, item['source'], item['id'] + ".item")
			with open(path, 'w', encoding="utf8") as f:
				f.write(s)

		else:
			# If the item is extant and still active, overwrite its values.
			prior_item = prior_items[item['id']]
			if prior_item['active']:
				populate_old(prior_item, item)
				# Remove the id from the list to track its continued presence
				# in the source's queue of new items.
				del prior_items[item['id']]

	# Any remaining extant items are considered old. Old items are removed
	# when they are both inactive and past their ttl date.
	now = timestamp.now()
	for prior_id, prior_item in prior_items.items():
		ttl_date = prior_item['created'] + prior_item['ttl']
		if not prior_item['active'] and ttl_date < now:
			del_count += 1
			file_path = os.path.join(DUNGEON_PATH, prior_item['source'], prior_item['id'] + ".item")
			os.remove(file_path)

	# Note update timestamp in state
	state['last_updated'] = timestamp.now()

	# Return counts
	return new_count, del_count

def populate_new(item):
	# id and source are required fields
	item['active'] = True
	if 'created' not in item: item['created'] = timestamp.now()
	if 'title' not in item: item['title'] = item['id']
	if 'link' not in item: item['link'] = None
	if 'time' not in item: item['time'] = None
	if 'author' not in item: item['author'] = None
	if 'body' not in item: item['body'] = None
	if 'tags' not in item: item['tags'] = [item['source']]
	if 'ttl' not in item: item['ttl'] = 0

def populate_old(prior, new):
	prior.set({
		'title': new['title'],
		'link': new['link'],
		'time': new['time'],
		'author': new['author'],
		'body': new['body'],
		'tags': new['tags'],
		'ttl': new['ttl'],
	})
