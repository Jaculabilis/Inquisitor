"""
Demonstrates the behavior of imports in sources.
"""
# Standard library imports
from datetime import datetime
import random

# Environment import
import flask

# Local import
from importdemohelper import secret

def fetch_new(state):
	return [{
		'source': 'importdemo',
		'id': '{:x}'.format(random.getrandbits(16 * 4)),
		'title': f'The secret is "{secret}"',
		'body': f'And flask\'s name is "{flask.__name__}"',
	}]
