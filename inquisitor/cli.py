# Standard library imports
import logging
import os

# Application imports
import dungeon as dungeonlib

# Globals
logger = logging.getLogger("inquisitor.cli")


def command_update(args):
	"""Fetch and store new items from the specified sources."""
	if not os.path.isdir(args.srcdir):
		print("update: Error: srcdir must be a directory")
		return (-1)
	if not os.path.isdir(args.dungeon):
		logger.error("update: Error: dungeon must be a directory")
		return (-1)
	if not args.sources:
		logger.error("update: Error: No sources specified")
		return (-1)

	# Initialize dungeon.
	dungeon = dungeonlib.Dungeon(args.dungeon)

	# Process each source argument.
	for source_arg in args.sources:
		dungeon.update(source_arg, args)

	return 0

def command_deactivate(args):
	"""Deactivate all items in the specified dungeon cells."""
	if not os.path.isdir(args.dungeon):
		logger.error("deactivate: Error: dungeon must be a directory")
		return (-1)
	if not args.sources:
		logger.error("deactivate: Error: No sources specified")
		return (-1)

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

	return 0
