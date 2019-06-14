"""
An example itemsource that produces an item with the current date.
ANy args provided will be added to the item body.
Fetch new items with `python inquisitor update --sources example`
or `--sources example:argument`.
"""
# Standard library imports
from datetime import date
import time

# Globals
SOURCE = "examplesource"


def fetch_new(state, args):
	now = date.today()
	item = create_item(
		SOURCE,
		'{}-{}-{}'.format(now.year, now.month, now.day),
		"Today is {}-{}-{}".format(now.year, now.month, now.day),
		ts=time.time(),
		body=args
	)
	return [item]
