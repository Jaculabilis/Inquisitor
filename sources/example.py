"""
An example itemsource that produces an item with the current date.
Fetch new items with `python inquisitor update --sources examplesource`.
"""
# Standard library imports
from datetime import date
import time

# Globals
SOURCE = "examplesource"


def fetch_new(state):
	now = date.today()
	item = {
		'id': '{}-{}-{}'.format(now.year, now.month, now.day),
		'source': SOURCE,
		'active': True,
		'time': time.time(),
		'created': time.time(),
		'title': "Today is {}-{}-{}".format(now.year, now.month, now.day),
		#'link':
		#'author':
		#'body':
	}
	return [item]
