"""
Demonstrates the behavior of the on_create and on_delete triggers.
The items it creates spawn dummy messages on creation and deletion.
It assumes the dungeon is located at ./dungeon.
"""
# Standard library imports
from datetime import datetime
import json
import random

def fetch_new(state):
	if state.get('return_item'):
		state['return_item'] = False
		return [{
			'source': 'triggerdemo',
			'id': 'triggerdemoitem',
			'title': 'This is the trigger demo item'
		}]
	else:
		state['return_item'] = True
		return []


def on_create(state, item):
	with open('dungeon/inquisitor/triggerdemo_create.item', 'w') as f:
		json.dump({
			'source': 'inquisitor',
			'id': 'triggerdemo_create',
			'title': 'Trigger demo on_create item',
			'active': True,
		}, f)


def on_delete(state, item):
	with open('dungeon/inquisitor/triggerdemo_delete.item', 'w') as f:
		json.dump({
			'source': 'inquisitor',
			'id': 'triggerdemo_delete',
			'title': 'Trigger demo on_delete item',
			'active': True,
		}, f)
