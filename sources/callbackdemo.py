"""
Demonstrates the behavior of the callback field.
"""
# Standard library imports
from datetime import datetime
import random

def fetch_new(state):
	itemid = '{:x}'.format(random.getrandbits(16 * 4))
	item = {
		'source': "callbackdemo",
		'id': itemid,
		'title': f"Callback demo",
		'body': 'No callbacks',
		'callback': { 'id': itemid }
	}
	return [item]

def callback(state, item):
	item['body'] = f"Last callback at {datetime.now()}"
