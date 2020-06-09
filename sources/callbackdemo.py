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
		'callback': { 'count': 0 }
	}
	return [item]

def callback(state, item):
	item['callback']['count'] += 1
	item['body'] = f"Last callback at {datetime.now()}, {item['callback']['count']} total callbacks"
