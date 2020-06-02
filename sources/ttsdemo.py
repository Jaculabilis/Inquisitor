"""
Demonstrates the behavior of the time-to-show item field.
On update, this source returns a new item with a tts of 30 seconds.
"""
# Standard library imports
from datetime import datetime
import random

def fetch_new(state):
	item = {
		'source': "ttsdemo",
		'id': '{:x}'.format(random.getrandbits(16 * 4)),
		'title': f"This item was created at {datetime.now()}",
		'tts': 30,
	}
	return [item]
