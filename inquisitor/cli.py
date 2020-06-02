# Standard library imports
import argparse
import json
import logging
import os
import random

# Application imports
from configs import logger, DUNGEON_PATH, SOURCES_PATH


def command_update(args):
	"""Fetch and store new items from the specified sources."""
	parser = argparse.ArgumentParser(
		prog="inquisitor update",
		description=command_update.__doc__,
		add_help=False)
	parser.add_argument("source",
		nargs="*",
		help="Sources to update.")
	args = parser.parse_args(args)

	if len(args.source) == 0:
		parser.print_help()
		return 0
	if not os.path.isdir(DUNGEON_PATH):
		logger.error("Couldn't find dungeon. Set INQUISITOR_DUNGEON or cd to parent folder of ./dungeon")
		return -1
	if not os.path.isdir(SOURCES_PATH):
		logger.error("Couldn't find sources. Set INQUISITOR_SOURCES or cd to parent folder of ./sources")

	# Update sources
	from importer import update_sources
	update_sources(*args.source)
	return 0


def command_deactivate(args):
	"""Deactivate all items in the specified dungeon cells."""
	parser = argparse.ArgumentParser(
		prog="inquisitor deactivate",
		description=command_deactivate.__doc__,
		add_help=False)
	parser.add_argument("source",
		nargs="*",
		help="Cells to deactivate.")
	parser.add_argument("--tag",
		help="Only deactivate items with this tag")
	parser.add_argument("--title",
		help="Only deactivate items with titles containing this substring")
	args = parser.parse_args(args)

	if len(args.source) == 0:
		parser.print_help()
		return 0
	if not os.path.isdir(DUNGEON_PATH):
		logger.error("Couldn't find dungeon. Set INQUISITOR_DUNGEON or cd to parent folder of ./dungeon")
		return -1

	# Deactivate all items in each source.
	from loader import load_items
	for source_name in args.source:
		path = os.path.join(DUNGEON_PATH, source_name)
		if not os.path.isdir(path):
			logger.warning("'{}' is not an extant source".format(source_name))
		count = 0
		items, _ = load_items(source_name)
		for item in items.values():
			if args.tag and args.tag not in item['tags']:
				continue
			if args.title and args.title not in item['title']:
				continue
			if item['active']:
				item['active'] = False
				count += 1
		logger.info("Deactivated {} items in '{}'".format(count, source_name))

	return 0


def command_add(args):
	"""Creates an item."""
	parser = argparse.ArgumentParser(
		prog="inquisitor add",
		description=command_add.__doc__,
		add_help=False)
	parser.add_argument("--id", help="String")
	parser.add_argument("--source", help="String")
	parser.add_argument("--title", help="String")
	parser.add_argument("--link", help="URL")
	parser.add_argument("--time", type=int, help="Unix timestmap")
	parser.add_argument("--author", help="String")
	parser.add_argument("--body", help="HTML")
	parser.add_argument("--tags", help="Comma-separated list")
	parser.add_argument("--ttl", type=int, help="Cleanup protection in seconds")
	parser.add_argument("--create", action="store_true", help="Create source if it doesn't exist")
	args = parser.parse_args(args)

	if not args.title:
		parser.print_help()
		return 0
	if not os.path.isdir(DUNGEON_PATH):
		logger.error("Couldn't find dungeon. Set INQUISITOR_DUNGEON or cd to parent folder of ./dungeon")
		return -1

	source = args.source or 'inquisitor'
	cell_path = os.path.join(DUNGEON_PATH, source)
	if not os.path.isdir(cell_path):
		if args.create:
			os.mkdir(cell_path)
		else:
			logger.error("Source '{}' does not exist".format(source))
			return -1

	from importer import populate_new
	item = {
		'id': '{:x}'.format(random.getrandbits(16 * 4)),
		'source': 'inquisitor'
	}
	if args.id: item['id'] = str(args.id)
	if args.source: item['source'] = str(args.source)
	if args.title: item['title'] = str(args.title)
	if args.link: item['link'] = str(args.link)
	if args.time: item['time'] = int(args.time)
	if args.author: item['author'] = str(args.author)
	if args.body: item['body'] = str(args.body)
	if args.tags: item['tags'] = [str(tag) for tag in args.tags.split(",")]
	if args.ttl: item['ttl'] = int(args.ttl)
	populate_new(item)

	s = json.dumps(item, indent=2)
	path = os.path.join(DUNGEON_PATH, item['source'], item['id'] + '.item')
	with open(path, 'w', encoding='utf8') as f:
		f.write(s)
	logger.info(item)


def command_feed(args):
	"""Print the current feed."""
	if not os.path.isdir(DUNGEON_PATH):
		logger.error("Couldn't find dungeon. Set INQUISITOR_DUNGEON or cd to parent folder of ./dungeon")
		return -1

	import shutil
	import loader
	import timestamp

	items, errors = loader.load_active_items()
	if not items and not errors:
		print("Feed is empty")
		return 0

	if errors:
		items.insert(0, {
			'id': 'read-errors',
			'title': '{} read errors'.format(len(errors)),
			'body': "\n".join(errors)
		})

	size = shutil.get_terminal_size((80, 20))
	width = min(80, size.columns)

	for item in items:
		title = item['title'] if 'title' in item else ""
		titles = [title]
		while len(titles[-1]) > width - 4:
			i = titles[-1][:width - 4].rfind(' ')
			titles = titles[:-1] + [titles[-1][:i].strip(), titles[-1][i:].strip()]
		print('+' + (width - 2) * '-' + '+')
		for title in titles:
			print("| {0:<{1}} |".format(title, width - 4))
		print("|{0:<{1}}|".format("", width - 2))
		info1 = ""
		if 'author' in title and item['author']:
			info1 += item['author'] + "  "
		if 'time' in item and item['time']:
			info1 += timestamp.stamp_to_readable(item['time'])
		print("| {0:<{1}} |".format(info1, width - 4))
		created = timestamp.stamp_to_readable(item['created']) if 'created' in item else ""
		info2 = "{0}  {1}  {2}".format(
			item['source'], item['id'], created)
		print("| {0:<{1}} |".format(info2, width - 4))
		print('+' + (width - 2) * '-' + '+')
		print()


def command_run(args):
	"""Run the default Flask server."""
	try:
		from app import app
		app.run()
		return 0
	except Exception as e:
		logger.error(e)
		return -1
