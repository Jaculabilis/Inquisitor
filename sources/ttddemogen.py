"""
Demonstrates the behavior of the time-to-die item field.
On update, this source creates a new item with a ttd of 30 in the cell
for the source ttddemoupd.
"""
# Standard library imports
from datetime import datetime
import random

def fetch_new(state):
	item = {
		'source': "ttddemoupd",
		'id': '{:x}'.format(random.getrandbits(16 * 4)),
		'title': f"This item was created at {datetime.now()}",
		'ttd': 30,
	}
	return [item]
