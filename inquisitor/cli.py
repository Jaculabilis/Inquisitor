# Standard library imports
import argparse
import logging
import os

# Application imports
import dungeon as dungeonlib

# Globals
logger = logging.getLogger("inquisitor.cli")


def parse_args(commands):
	parser = argparse.ArgumentParser()
	parser.add_argument("command", default="help", help="The command to execute", choices=list(commands.keys()))
	parser.add_argument("--srcdir", help="Path to sources folder (default ./sources)", default="./sources")
	parser.add_argument("--dungeon", help="Path to item cache folder (default ./dungeon)", default="./dungeon")
	parser.add_argument("--sources", help="Sources to update, by name", nargs="*")
	parser.add_argument("--log", default="INFO", help="Set the log level (default: INFO)")

	args = parser.parse_args()

	if not os.path.isdir(args.srcdir):
		print("Error: srcdir must be a directory")
		exit(-1)
	if not os.path.isdir(args.dungeon):
		logger.error("Error: dungeon must be a directory")
		exit(-1)
	if not args.sources:
		logger.error("Error: No sources specified")
		exit(-1)

	return args


def run():
	# Enumerate valid commands.
	g = globals()
	commands = {
		name[8:] : g[name]
		for name in g
		if name.startswith("command_")}

	args = parse_args(commands)

	# Configure logging.
	loglevel = getattr(logging, args.log.upper())
	if not isinstance(loglevel, int):
		raise ValueError("Invalid log level: {}".format(args.log))
	logging.basicConfig(format='[%(levelname)s:%(filename)s:%(lineno)d] %(message)s', level=loglevel)

	# Execute command.
	commands[args.command](args)


def command_update(args):
	"""Fetches new items from sources and stores them in the dungeon."""
	# Initialize dungeon.
	dungeon = dungeonlib.Dungeon(args.dungeon)

	# Process each source argument.
	for source_arg in args.sources:
		dungeon.update(source_arg, args)


def command_deactivate(args):
	"""Deactivates all items in the given sources."""
	# Initialize dungeon.
	dungeon = dungeonlib.Dungeon(args.dungeon)

	# Deactivate all items in each source.
	for source_name in args.sources:
		if source_name not in dungeon:
			print("Error: No source named '{}'".format(source_name))
			print("Valid source names are: " + " ".join([s for s in dungeon]))
			continue
		cell = dungeon[source_name]
		count = 0
		for item_id in cell:
			item = cell[item_id]
			if item['active']:
				item.deactivate()
				count += 1
		logger.info("Deactivated {} items in '{}'".format(count, source_name))
