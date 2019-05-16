# Standard library imports
import importlib.util
import os
import logging

# Globals
logger = logging.getLogger("inquisitor.core")


def load_source_module(source_path):
	"""Loads a source module and checks for necessary members."""
	logger.debug("load_source_module('{}')".format(source_path))
	spec = importlib.util.spec_from_file_location("itemsource", source_path)
	itemsource = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(itemsource)
	if not hasattr(itemsource, 'SOURCE'):
		raise ImportError("SOURCE missing")
	if not hasattr(itemsource, 'fetch_new'):
		raise ImportError("fetch_new missing")
	return itemsource


def load_all_sources(source_folder):
	"""Loads all source modules in the given folder."""
	# Navigate to the sources folder
	cwd = os.getcwd()
	os.chdir(source_folder)
	# Load all sources
	source_names = [
		filename
		for filename in os.listdir()
		if filename.endswith(".py")]
	sources = []
	for source_name in source_names:
		try:
			itemsource = load_source_module(source_name)
			sources.append(itemsource)
		except ImportError as e:
			logger.error("Error importing {}: {}".format(source_name, e))
	# Return to cwd
	os.chdir(cwd)
	return sources
