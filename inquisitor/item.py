# Standard library imports
import importlib.util
import os
import logging
import time


# Globals
logger = logging.getLogger("inquisitor.item")


def create_item(source, item_id, title, link=None, time=None, author=None, body=None):
	item = {
		'id': item_id,
		'source': source,
		'active': True,
		'created': time.time(),
		'title': title,
	}
	if link is not None:
		item['link'] = link
	if time is not None:
		item['time'] = time
	if author is not None:
		item['author'] = author
	if body is not None:
		item['body'] = body
	return item
