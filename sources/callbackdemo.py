"""
Demonstrates the behavior of the callback field.
"""
# Standard library imports
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
	print(item)
