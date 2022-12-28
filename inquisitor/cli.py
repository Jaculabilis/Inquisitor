# Standard library imports
import argparse
import json
import logging
import os
import random
import sys

# Application imports
from inquisitor.configs import logger, DUNGEON_PATH, SOURCES_PATH, add_logging_handler


def command_test(args):
    """Echo config file values."""
    from inquisitor.configs.resolver import (
        config_path,
        CONFIG_DATA,
        data_path,
        CONFIG_SOURCES,
        source_path,
        CONFIG_CACHE,
        cache_path,
        CONFIG_LOGFILE,
        log_file,
        CONFIG_VERBOSE,
        is_verbose,
        CONFIG_SUBFEEDS,
        subfeeds,
    )

    subfeeds = (
        "; ".join(
            "{0}: {1}".format(sf_name, " ".join(sf_sources))
            for sf_name, sf_sources in subfeeds.items()
        )
        if subfeeds
        else ""
    )
    print(f"Inquisitor configured from {config_path}")
    print(f"    {CONFIG_DATA} = {data_path}")
    print(f"    {CONFIG_SOURCES} = {source_path}")
    print(f"    {CONFIG_CACHE} = {cache_path}")
    print(f"    {CONFIG_LOGFILE} = {log_file}")
    print(f"    {CONFIG_VERBOSE} = {is_verbose}")
    print(f"    {CONFIG_SUBFEEDS} = {subfeeds}")
    return 0


def command_update(args):
    """Fetch and store new items from the specified sources."""
    parser = argparse.ArgumentParser(
        prog="inquisitor update", description=command_update.__doc__, add_help=False
    )
    parser.add_argument("source", nargs="*", help="Sources to update.")
    args = parser.parse_args(args)

    if len(args.source) == 0:
        parser.print_help()
        return 0
    if not os.path.isdir(DUNGEON_PATH):
        logger.error(
            "Couldn't find dungeon. Set INQUISITOR_DUNGEON or cd to parent folder of ./dungeon"
        )
        return -1
    if not os.path.isdir(SOURCES_PATH):
        logger.error(
            "Couldn't find sources. Set INQUISITOR_SOURCES or cd to parent folder of ./sources"
        )

    # Update sources
    from inquisitor.sources import update_sources

    update_sources(*args.source)
    return 0


def command_deactivate(args):
    """Deactivate all items in the specified dungeon cells."""
    parser = argparse.ArgumentParser(
        prog="inquisitor deactivate",
        description=command_deactivate.__doc__,
        add_help=False,
    )
    parser.add_argument("source", nargs="*", help="Cells to deactivate.")
    parser.add_argument("--tag", help="Only deactivate items with this tag")
    parser.add_argument(
        "--title", help="Only deactivate items with titles containing this substring"
    )
    args = parser.parse_args(args)

    if len(args.source) == 0:
        parser.print_help()
        return 0
    if not os.path.isdir(DUNGEON_PATH):
        logger.error(
            "Couldn't find dungeon. Set INQUISITOR_DUNGEON or cd to parent folder of ./dungeon"
        )
        return -1

    # Deactivate all items in each source.
    from inquisitor.loader import load_items

    for source_name in args.source:
        path = os.path.join(DUNGEON_PATH, source_name)
        if not os.path.isdir(path):
            logger.warning("'{}' is not an extant source".format(source_name))
        count = 0
        items, _ = load_items(source_name)
        for item in items.values():
            if args.tag and args.tag not in item["tags"]:
                continue
            if args.title and args.title not in item["title"]:
                continue
            if item["active"]:
                item["active"] = False
                count += 1
        logger.info("Deactivated {} items in '{}'".format(count, source_name))

    return 0


def command_add(args):
    """Creates an item."""
    parser = argparse.ArgumentParser(
        prog="inquisitor add", description=command_add.__doc__, add_help=False
    )
    parser.add_argument("--id", help="String")
    parser.add_argument("--source", help="String")
    parser.add_argument("--title", help="String")
    parser.add_argument("--link", help="URL")
    parser.add_argument("--time", type=int, help="Unix timestmap")
    parser.add_argument("--author", help="String")
    parser.add_argument("--body", help="HTML")
    parser.add_argument("--tags", help="Comma-separated list")
    parser.add_argument("--ttl", type=int, help="Cleanup protection in seconds")
    parser.add_argument("--ttd", type=int, help="Cleanup force in seconds")
    parser.add_argument("--tts", type=int, help="Display delay in seconds")
    parser.add_argument(
        "--create", action="store_true", help="Create source if it doesn't exist"
    )
    args = parser.parse_args(args)

    if not args.title:
        parser.print_help()
        return 0
    if not os.path.isdir(DUNGEON_PATH):
        logger.error(
            "Couldn't find dungeon. Set INQUISITOR_DUNGEON or cd to parent folder of ./dungeon"
        )
        return -1

    source = args.source or "inquisitor"
    cell_path = os.path.join(DUNGEON_PATH, source)
    if args.create:
        from inquisitor.sources import ensure_cell

        ensure_cell(source)
    elif not os.path.isdir(cell_path):
        logger.error("Source '{}' does not exist".format(source))
        return -1

    item = {
        "id": args.id or "{:x}".format(random.getrandbits(16 * 4)),
        "source": source,
    }
    if args.title:
        item["title"] = str(args.title)
    if args.link:
        item["link"] = str(args.link)
    if args.time:
        item["time"] = int(args.time)
    if args.author:
        item["author"] = str(args.author)
    if args.body:
        item["body"] = str(args.body)
    if args.tags:
        item["tags"] = [str(tag) for tag in args.tags.split(",")]
    if args.ttl:
        item["ttl"] = int(args.ttl)
    if args.ttd:
        item["ttd"] = int(args.ttd)
    if args.tts:
        item["tts"] = int(args.tts)

    from inquisitor.loader import new_item

    saved_item = new_item(source, item)
    logger.info(saved_item)


def command_feed(args):
    """Print the current feed."""
    if not os.path.isdir(DUNGEON_PATH):
        logger.error(
            "Couldn't find dungeon. Set INQUISITOR_DUNGEON or cd to parent folder of ./dungeon"
        )
        return -1

    import shutil
    from inquisitor import loader
    from inquisitor import timestamp

    items, errors = loader.load_active_items(source_names=None)
    if not items and not errors:
        print("Feed is empty")
        return 0

    if errors:
        items.insert(
            0,
            {
                "title": "{} read errors: {}".format(len(errors), " ".join(errors)),
                "body": "\n".join(errors),
            },
        )

    size = shutil.get_terminal_size((80, 20))
    width = min(80, size.columns)

    for item in items:
        title = item["title"] if "title" in item else ""
        titles = [title]
        while len(titles[-1]) > width - 4:
            i = titles[-1][: width - 4].rfind(" ")
            titles = titles[:-1] + [titles[-1][:i].strip(), titles[-1][i:].strip()]
        print("+" + (width - 2) * "-" + "+")
        for title in titles:
            print("| {0:<{1}} |".format(title, width - 4))
        print("|{0:<{1}}|".format("", width - 2))
        info1 = ""
        if "author" in title and item["author"]:
            info1 += item["author"] + "  "
        if "time" in item and item["time"]:
            info1 += timestamp.stamp_to_readable(item["time"])
        print("| {0:<{1}} |".format(info1, width - 4))
        created = (
            timestamp.stamp_to_readable(item["created"]) if "created" in item else ""
        )
        info2 = "{0}  {1}  {2}".format(
            item.get("source", ""), item.get("id", ""), created
        )
        print("| {0:<{1}} |".format(info2, width - 4))
        print("+" + (width - 2) * "-" + "+")
        print()


def command_run(args):
    """Run the default Flask server."""
    parser = argparse.ArgumentParser(
        prog="inquisitor run", description=command_run.__doc__, add_help=False
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args(args)

    try:
        from inquisitor.app import app

        app.run(port=args.port, debug=args.debug)
        return 0
    except Exception as e:
        logger.error(e)
        return -1


def command_help(args):
    """Print this help message and exit."""
    print_usage()
    return 0


def nocommand(args):
    print("command required")
    return 0


def main():
    """CLI entry point"""
    # Enable piping
    from signal import signal, SIGPIPE, SIG_DFL

    signal(SIGPIPE, SIG_DFL)

    # Collect the commands from this module
    import inquisitor.cli

    commands = {
        name[8:]: func
        for name, func in vars(inquisitor.cli).items()
        if name.startswith("command_")
    }
    descriptions = "\n".join(
        ["- {0}: {1}".format(name, func.__doc__) for name, func in commands.items()]
    )

    # Set up the parser
    parser = argparse.ArgumentParser(
        description="Available commands:\n{}\n".format(descriptions),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        help="The command to execute",
        choices=commands,
        metavar="command",
    )
    parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Command arguments", metavar="args"
    )
    parser.add_argument(
        "-v", action="store_true", dest="verbose", help="Enable debug logging"
    )

    # Extract the usage print for command_help
    global print_usage
    print_usage = parser.print_help

    args = parser.parse_args()

    # Initialize a console logger
    add_logging_handler(verbose=args.verbose, log_filename=None)

    # Execute command
    try:
        command = commands.get(args.command, nocommand)
        sys.exit(command(args.args))
    except BrokenPipeError:
        # See https://docs.python.org/3.10/library/signal.html#note-on-sigpipe
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
