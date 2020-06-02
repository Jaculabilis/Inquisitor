"""
Demonstrates the behavior of the time-to-live item field.
This source does not generate items. It is solely for use with the
ttldemogen source, which creats new items for it. This source can be
updated to cause a removal check on inactive items created by
ttldemogen.
"""
# Standard library imports
from datetime import datetime
import random

def fetch_new(state):
	return []
