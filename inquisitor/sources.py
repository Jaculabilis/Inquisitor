import os
import traceback
import importlib.util
import json
import sys


from inquisitor import loader, timestamp, error
from inquisitor.configs import SOURCES_PATH, DUNGEON_PATH, logger


USE_NEWEST = (
	'title',
	'tags',
	'link',
	'time'
	'author',
	'body',
	'ttl',
	'ttd',
	'tts',
)


class InquisitorStubSource:
	"""A dummy source-like object for clearing out ad-hoc inquisitor items"""
	def fetch_new(self, state):
		return []


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
			update_source(source_name, source_module)
		except Exception:
			error.as_item(
				f'Error updating source "{source_name}"',
				traceback.format_exc())


def load_source(source_name):
	"""
	Attempts to load the source module with the given name.
	Raises an exception on failure.
	"""
	if source_name == 'inquisitor':
		return InquisitorStubSource()

	cwd = os.getcwd()
	try:
		# Push the sources directory.
		os.chdir(SOURCES_PATH)
		# Make the sources directory importable while working with sources.
		if SOURCES_PATH not in sys.path:
			sys.path.insert(0, SOURCES_PATH)

		# Check if the named source is present.
		source_file_name = source_name + '.py'
		if not os.path.isfile(source_file_name):
			raise FileNotFoundError(f'Missing "{source_name}" in "{SOURCES_PATH}"')

		# Import the source module by file path.
		logger.debug(f'Loading module "{source_file_name}"')
		spec = importlib.util.spec_from_file_location(source_name, source_file_name)
		itemsource = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(itemsource)
		itemsource = importlib.import_module(source_name)

		# Require fetch_new().
		if not hasattr(itemsource, 'fetch_new'):
			raise ImportError(f'Missing fetch_new in "{source_file_name}"')

		return itemsource

	finally:
		os.chdir(cwd)
		if SOURCES_PATH in sys.path:
			sys.path.remove(SOURCES_PATH)


def update_source(source_name, source):
	"""
	Attempts to update the given source. Raises an exception if the source does.
	"""
	# Get a list of item ids that already existed in this source's cell.
	prior_ids = loader.get_item_ids(source_name)
	logger.debug(f'Found {len(prior_ids)} prior items')

	# Get the feed items from the source's fetch method.
	state = loader.load_state(source_name)
	fetched = source.fetch_new(state)
	state.flush()
	logger.debug(f'Fetched {len(fetched)} items')
	fetched_items = {item['id']: item for item in fetched}

	# Determine which items are new and which are updates.
	# We query the file system here instead of checking against this source's
	# item ids from above because sources are allowed to generate in other
	# sources' cells.
	new_items = []
	updated_items = []
	for item in fetched:
		item_source = item.get('source', source_name)
		if loader.item_exists(item_source, item['id']):
			updated_items.append(item)
		else:
			new_items.append(item)

	# Write all the new items to the source's cell.
	has_create_handler = hasattr(source, 'on_create')
	for item in new_items:
		item_source = item.get('source', source_name)
		created_item = loader.new_item(item_source, item)
		if has_create_handler:
			# Because some sources do not return items more than once,
			# exceptions in the on-create handler must be squashed.
			try:
				source.on_create(state, created_item)
			except:
				error.as_item(
					f'Exception in {source_name}.on_create',
					traceback.format_exc())

	# Update the other items using the fetched items' values.
	for new_item in updated_items:
		old_item = loader.load_item(new_item['source'], new_item['id'])
		for field in USE_NEWEST:
			if field in new_item and old_item[field] != new_item[field]:
				old_item[field] = new_item[field]
		if 'callback' in new_item:
			old_callback = old_item.get('callback', {})
			# Because of the way this update happens, any fields that are set
			# in the callback when the item is new will keep their original
			# values, as those values reappear in new_item on subsequent
			# updates.
			old_item['callback'] = {**old_item['callback'], **new_item['callback']}

	# In general, items are removed when they are old (not found in the last
	# fetch) and inactive. Some item fields can change this basic behavior.
	del_count = 0
	now = timestamp.now()
	has_delete_handler = hasattr(source, 'on_delete')
	fetched_ids = [item['id'] for item in updated_items]
	old_item_ids = [
		item_id for item_id in prior_ids
		if item_id not in fetched_ids]
	for item_id in old_item_ids:
		item = loader.load_item(source_name, item_id)
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
			try:
				if has_delete_handler:
					# Run the delete handler so exceptions prevent deletions
					source.on_delete(state, item)
				loader.delete_item(source_name, item['id'])
				del_count += 1
			except:
				error.as_item(
					f'Failed to delete {source_name}/{item["id"]}',
					traceback.format_exc())

	# Note update timestamp in state
	state['last_updated'] = timestamp.now()

	# Log counts
	logger.info("{} new item{}, {} deleted item{}".format(
		len(new_items), "s" if len(new_items) != 1 else "",
		del_count, "s" if del_count != 1 else ""))


def item_callback(source_name, itemid):
	try:
		# Load the module with the callback function
		source_module = load_source(source_name)
		if not hasattr(source_module, 'callback'):
			raise ImportError(f"Missing callback in '{source_name}'")
		# Load the source state and the origin item
		state = loader.load_state(source_name)
		item = loader.load_item(source_name, itemid)
		# Execute callback
		source_module.callback(state, item)
		# Save any changes
		item.flush()
		state.flush()
	except Exception:
		error.as_item(
			f"Error executing callback for {source_name}/{itemid}",
			traceback.format_exc())
