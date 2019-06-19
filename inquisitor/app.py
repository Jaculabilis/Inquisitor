# Standard library imports
import datetime
import logging

# Third party imports
from flask import Flask, render_template, request, jsonify

# Application imports
import dungeon as dungeonlib

# Globals
logger = logging.getLogger("inquisitor.app")
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s %(levelname)s:%(filename)s:%(lineno)d] %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

app = Flask(__name__)
dungeon = dungeonlib.Dungeon("dungeon")


def list_filter(whitelist=None, blacklist=None):
	if whitelist is not None:
		return lambda item: any([tag in whitelist for tag in item['tags']])
	if blacklist is not None:
		return lambda item: not any([tag in blacklist for tag in item['tags']])
	return lambda s: True

@app.template_filter("datetimeformat")
def datetimeformat(value, formatstr="%Y-%m-%d %H:%M:%S"):
	if value is None:
		return ""
	dt = datetime.datetime.fromtimestamp(value)
	return dt.strftime(formatstr)

@app.route("/")
def root():
	dungeon = dungeonlib.Dungeon("dungeon")
	filter_lambda = list_filter(
		whitelist=request.args.get('only'),
		blacklist=request.args.get('not'))
	active_items = []
	for cell_name in dungeon:
		cell = dungeon[cell_name]
		for item_id in cell:
			try:
				item = cell[item_id]
			except:
				logger.error("Exception reading {}/{}".format(cell_name, item_id))
				continue
			if item['active'] and filter_lambda(item):
					active_items.append(item)
	logger.info("Found {} active items".format(len(active_items)))
	return render_template("feed.html", items=active_items[:100])


@app.route("/deactivate/", methods=['POST'])
def deactivate():
	params = request.get_json()
	if 'source' not in params and 'itemid' not in params:
		logger.error("Bad request params: {}".format(params))
	item = dungeon[params['source']][params['itemid']]
	item.deactivate()
	return jsonify({'active': item['active']})

