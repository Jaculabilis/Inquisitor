"""
An example itemsource that produces an item with the current date.
Fetch new items with `python inquisitor update --sources example`
"""
# Standard library imports
from datetime import date
import time


def fetch_new(state):
	now = date.today()
	item = {
		'source': "example",
		'id': '{}-{}-{}'.format(now.year, now.month, now.day),
		'title': "Today is {}-{}-{}".format(now.year, now.month, now.day),
	}
	return [item]
