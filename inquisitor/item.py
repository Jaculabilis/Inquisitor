# Standard library imports
import importlib.util
import os
import logging

# Globals
logger = logging.getLogger("inquisitor.item")


def create_item(source, item_id, title, link=None, ts=None, author=None, body=None, tags=None):
	import time
	item = {
		'id': item_id,
		'source': source,
		'active': True,
		'created': time.time(),
		'title': title,
		'link': link,
		'time': ts,
		'author': author,
		'body': body,
		'tags': [] if tags is None else tags,
	}
	return item

import builtins
builtins.create_item = create_item
