import os
import logging

DUNGEON_PATH = os.path.abspath(os.environ.get("INQUISITOR_DUNGEON") or "./dungeon")
SOURCES_PATH = os.path.abspath(os.environ.get("INQUISITOR_SOURCES") or "./sources")
CACHE_PATH = os.path.abspath(os.environ.get("INQUISITOR_CACHE") or "./cache")

logger = logging.getLogger("inquisitor")
handler = logging.StreamHandler()
logger.addHandler(handler)

def log_normal():
	logger.setLevel(logging.INFO)
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter('[{levelname}] {message}', style="{")
	handler.setFormatter(formatter)

def log_verbose():
	logger.setLevel(logging.DEBUG)
	handler.setLevel(logging.DEBUG)
	formatter = logging.Formatter('[{asctime}] [{levelname}:{filename}:{lineno}] {message}', style="{")
	handler.setFormatter(formatter)

log_normal()
