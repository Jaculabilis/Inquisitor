# Standard library imports
import argparse
import os
import logging
import sys

# Application imports
import cli

# Globals
logger = logging.getLogger("inquisitor.__main__")


def parse_args(valid_commands):
	command_descs = "\n".join([
		"- {0}: {1}".format(name, func.__doc__)
		for name, func in valid_commands.items()])
	parser = argparse.ArgumentParser(description="Available commands:\n{}\n".format(command_descs), formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument("command", default="help", help="The command to execute", choices=valid_commands, metavar="COMMAND")
	parser.add_argument("--srcdir", help="Path to sources folder (default ./sources)", default="./sources")
	parser.add_argument("--dungeon", help="Path to item cache folder (default ./dungeon)", default="./dungeon")
	parser.add_argument("--sources", help="Sources to update, by name", nargs="*")
	parser.add_argument("--log", default="INFO", help="Set the log level (default: INFO)")

	args = parser.parse_args()

	return args


def run_flask_server(args):
	"""Run the default flask server serving from the specified dungeon."""
	try:
		from app import app
		app.run()
		return 0
	except Exception as e:
		logger.error(e)
		return (-1)


def main():
	# Enumerate valid commands.
	commands = {
		name[8:] : func
		for name, func in vars(cli).items()
		if name.startswith("command_")}
	commands["run"] = run_flask_server

	args = parse_args(commands)

	# Configure logging.
	loglevel = getattr(logging, args.log.upper())
	if not isinstance(loglevel, int):
		raise ValueError("Invalid log level: {}".format(args.log))
	logging.basicConfig(format='[%(levelname)s:%(filename)s:%(lineno)d] %(message)s', level=loglevel)

	# Execute command.
	if args.command:
		return commands[args.command](args)


if __name__ == "__main__":
	sys.exit(main())
