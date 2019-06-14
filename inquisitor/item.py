# Standard library imports
import importlib.util
import os
import logging

# Globals
logger = logging.getLogger("inquisitor.item")


def create_item(source, item_id, title, link=None, ts=None, author=None, body=None):
	import time
	item = {
		'id': item_id,
		'source': source,
		'active': True,
		'created': time.time(),
		'title': title,
	}
	if link is not None:
		item['link'] = link
	if ts is not None:
		item['time'] = ts
	if author is not None:
		item['author'] = author
	if body is not None:
		item['body'] = body
	return item

import builtins
builtins.create_item = create_item
