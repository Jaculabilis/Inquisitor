"""
Generates a dummy item.
"""
# Standard library imports
from datetime import datetime
import inspect
import logging
import os
import random
from time import sleep
import sys

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


class RedditScraper:
	"""
	An engine for generating items from subreddits.
	"""
	@staticmethod
	def fetch_new(state, name, reddit):
		items = []
		for name, obj in inspect.getmembers(sys.modules[name]):
			if (inspect.isclass(obj)
				and issubclass(obj, RedditScraper)
				and obj is not RedditScraper
			):
				sub_items = obj(reddit).get_items()
				items.extend(sub_items)
		return items

	def __init__(self, reddit):
		self.reddit = reddit

	def get_items(self):
		sub_name = self.subreddit_name
		logger.info(f'Fetching posts from r/{sub_name}')
		subreddit = self.reddit.subreddit(sub_name)
		posts = self.subreddit_page(subreddit)
		items = []
		for post in posts:
			if self.filter_post(post):
				items.append(self.item_from_post(post))
		return items

	def item_from_post(self, post):
		item = {
			'source': self.source,
			'id': post.id,
			'title': self.get_title(post),
			'link': self.get_link(post),
			'time': post.created_utc,
			'author': '/u/' + (post.author.name if post.author else "[deleted]"),
			'body': self.get_body(post),
			'tags': self.get_tags(post),
			'ttl': self.get_ttl(post),
		}
		ttl = self.get_ttl(post)
		if ttl is not None: item['ttl'] = ttl
		ttd = self.get_ttd(post)
		if ttd is not None: item['ttd'] = ttd
		tts = self.get_tts(post)
		if tts is not None: item['tts'] = tts
		callback = self.get_callback(post)
		if callback is not None: item['callback'] = callback
		return item

	def subreddit_page(self, subreddit):
		return subreddit.hot(limit=25)

	def filter_post(self, post):
		return True

	def get_title(self, post):
		s = '[S] ' if post.spoiler else ''
		nsfw = '[NSFW] ' if post.over_18 else ''
		return f'{s}{nsfw}/{post.subreddit_name_prefixed}: {post.title}'

	def get_link(self, post):
		return f'https://reddit.com{post.permalink}'

	def get_body(self, post):
		parts = []
		if not post.is_self:
			parts.append(f'<a href="{post.url}">link post</a>')
		if hasattr(post, 'preview'):
			try:
				previews = post.preview['images'][0]['resolutions']
				small_previews = [p for p in previews if p['width'] < 800]
				preview = sorted(small_previews, key=lambda p:-p['width'])[0]
				parts.append(f'<img src="{preview["url"]}">')
			except:
				pass
		if post.selftext:
			limit = post.selftext[1024:].find(' ')
			preview_body = post.selftext[:1024 + limit]
			if len(preview_body) < len(post.selftext):
				preview_body += '[...]'
			parts.append(f'<p>{preview_body}</p>')
		return '<br><hr>'.join(parts)

	def get_tags(self, post):
		tags = ['reddit', post.subreddit_name_prefixed[2:]]
		if post.over_18:
			tags.append('nsfw')
		return tags

	def get_ttl(self, post):
		return 60 * 60 * 24 * 7  # 1 week

	def get_ttd(self, post):
		return None

	def get_tts(self, post):
		return None

	def get_callback(self, post):
		return None

	def callback(self, state, item):
		raise NotImplementedError('callback')

	def on_create(self, state, item):
		raise NotImplementedError('on_create')

	def on_delete(self, state, item):
		raise NotImplementedError('on_delete')
