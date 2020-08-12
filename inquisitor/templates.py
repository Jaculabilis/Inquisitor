"""
Generates a dummy item.
"""
# Standard library imports
from datetime import datetime
import logging
import os
import random
from time import sleep

# Third-party library imports
from bs4 import BeautifulSoup
import requests

# Module imports
from inquisitor import CACHE_PATH

logger = logging.getLogger('inquisitor.templates')


def cache_image(source, url, filename):
	# Define some paths
	path = os.path.join(CACHE_PATH, source)
	file_path = os.path.join(path, filename)
	cached_url = f'/cache/{source}/{filename}'
	# Ensure cache folder
	if not os.path.isdir(path):
		os.mkdir(path)
	# Fetch url
	logger.info(f'Caching {url} to {file_path}')
	response = requests.get(url)
	# Write file to disk
	with open(file_path, 'wb') as f:
		f.write(response.content)
	# Return the inquisitor path to the file
	return cached_url


class LinearCrawler:
	"""
	An engine for generating items from web sources that link content
	together in a linear fashion, such as webcomics.
	"""
	def fetch_new(self, state):
		items = []
		max_iter = self.max_iterations() - 1
		new = self.try_fetch(state)
		items.extend(new)
		for iter in range(max_iter):
			sleep(1)
			# If we've already gotten some items out of this fetch, we don't
			# want to lose them and have the state still be set to the next
			# page, so we wrap further calls in a try block and force return
			# if we hit an error.
			try:
				new = self.try_fetch(state)
			except:
				new = []
			items.extend(new)
			# Cut out early if there was nothing returned
			if not new:
				break
		return items

	def try_fetch(self, state):
		# Check for whether a new page should be crawled
		if 'current_page' not in state:
			next_page = self.get_start_url()
		else:
			current = state['current_page']
			response = requests.get(current)
			soup = BeautifulSoup(response.text, features='html.parser')
			next_page = self.get_next_page_url(current, soup)
		if not next_page:
			return []  # nothing new

		# Download the new page
		logger.info('Fetching ' + next_page)
		response = requests.get(next_page)
		soup = BeautifulSoup(response.text, features="html.parser")

		# Create an item from the page
		item = self.make_item(next_page, soup)

		# Update the state and return the item
		state['current_page'] = next_page
		return [item]

	def max_iterations(self):
		return 3

	def get_start_url(self):
		raise NotImplementedError('get_start_url is required')

	def get_next_page_url(self, url, soup):
		raise NotImplementedError('get_next_page_url is required')

	def make_item(self, url, soup):
		raise NotImplementedError('make_item is required')
