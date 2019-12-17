import os
import logging

DUNGEON_PATH = os.path.abspath(os.environ.get("INQUISITOR_DUNGEON") or "./dungeon")
SOURCES_PATH = os.path.abspath(os.environ.get("INQUISITOR_SOURCES") or "./sources")

logger = logging.getLogger("inquisitor")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[{levelname}] {message}', style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)
