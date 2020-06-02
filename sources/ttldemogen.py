"""
Demonstrates the behavior of the time-to-live item field.
On update, this source creates a new item with a ttl of 30 in the cell
for the source ttldemoupd.
"""
# Standard library imports
from datetime import datetime
import random

def fetch_new(state):
	item = {
		'source': "ttldemoupd",
		'id': '{:x}'.format(random.getrandbits(16 * 4)),
		'title': f"This item was created at {datetime.now()}",
		'ttl': 30,
	}
	return [item]
