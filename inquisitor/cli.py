# Standard library imports
import argparse
import logging
import os

# Application imports
from core import load_all_sources
from dungeon import Dungeon

# Globals
logger = logging.getLogger("inquisitor.cli")


def run():
	parser = argparse.ArgumentParser()
	parser.add_argument("--log", default="INFO", help="Set the log level (default: INFO)")
	subparsers = parser.add_subparsers(help="Command to execute", dest="command")
	subparsers.required = True

	update_parser = subparsers.add_parser("update", help="Fetch new items")
	update_parser.add_argument("--srcdir", help="Path to sources folder (default ./sources)",
		default="./sources")
	update_parser.add_argument("--dungeon", help="Path to item cache folder (default ./dungeon)",
		default="./dungeon")
	update_parser.add_argument("--sources", help="Sources to update, by name",
		nargs="*")
	update_parser.set_defaults(func=update)

	args = parser.parse_args()

	# Configure logging
	loglevel = getattr(logging, args.log.upper())
	if not isinstance(loglevel, int):
		raise ValueError("Invalid log level: {}".format(args.log))
	logging.basicConfig(format='[%(levelname)s:%(filename)s:%(lineno)d] %(message)s', level=loglevel)

	args.func(args)


def update(args):
	"""Fetches new items from sources and stores them in the dungeon."""
	if not os.path.isdir(args.srcdir):
		logger.error("srcdir must be a directory")
		exit(-1)
	if not os.path.isdir(args.dungeon):
		logger.error("dungeon must be a directory")
		exit(-1)
	sources = load_all_sources(args.srcdir)
	source_names = [s.SOURCE for s in sources]
	if args.sources:
		names = args.sources
		for name in names:
			if name not in source_names:
				logger.error("Source not found: {}".format(name))
	else:
		names = source_names
	dungeon = Dungeon(args.dungeon)
	for itemsource in sources:
		if itemsource.SOURCE in names:
			new_items = dungeon.update(itemsource)
			items = dungeon.get_active_items_for_folder(itemsource.SOURCE)
			logger.info("{} new item{}".format(new_items, "s" if new_items != 1 else ""))
