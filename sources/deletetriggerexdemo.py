"""
Demonstrates the behavior of exceptions in create/delete triggers.
To allow for deletions, it alternates returning a single item and
returning nothing.
"""
# Standard library imports
from datetime import datetime
import json
import random

def fetch_new(state):
	if state.get('return_item'):
		state['return_item'] = False
		return [{
			'source': 'deletetriggerexdemo',
			'id': 'deletetriggerexdemoitem',
			'title': 'Delete trigger exception demo'
		}]
	else:
		state['return_item'] = True
		return []


def on_create(state, item):
	raise Exception('on_create')


def on_delete(state, item):
	raise Exception('on_delete')
