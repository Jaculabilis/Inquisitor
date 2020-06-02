# Standard library imports
import argparse

# Application imports
import cli
import configs


from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL) 


def parse_args(valid_commands):
	command_descs = "\n".join([
		"- {0}: {1}".format(name, func.__doc__)
		for name, func in valid_commands.items()])
	parser = argparse.ArgumentParser(
		description="Available commands:\n{}\n".format(command_descs),
		formatter_class=argparse.RawDescriptionHelpFormatter,
		add_help=False)
	parser.add_argument("command",
		nargs="?",
		default="help",
		help="The command to execute",
		choices=valid_commands,
		metavar="command")
	parser.add_argument("args",
		nargs=argparse.REMAINDER,
		help="Command arguments",
		metavar="args")
	parser.add_argument("-v",
		action="store_true",
		dest="verbose",
		help="Enable debug logging")

	global print_usage
	print_usage = parser.print_help

	return parser.parse_args()

def command_help(args):
	"""Print this help message and exit."""
	print_usage()
	return 0

def main():
	# Enumerate valid commands.
	commands = {
		name[8:] : func
		for name, func in vars(cli).items()
		if name.startswith("command_")}
	commands['help'] = command_help

	args = parse_args(commands)

	# Configure logging.
	if args.verbose:
		configs.log_verbose()

	# Execute command.
	if args.command:
		return commands[args.command](args.args)


if __name__ == "__main__":
	import sys
	sys.exit(main())
