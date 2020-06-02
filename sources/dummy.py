"""
Generates a dummy item.
"""
# Standard library imports
from datetime import datetime
import random

def fetch_new(state):
	item = {
		'source': "dummy",
		'id': '{:x}'.format(random.getrandbits(16 * 4)),
		'title': str(datetime.now()),
	}
	return [item]
