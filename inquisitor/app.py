# Standard library imports
from datetime import datetime
import logging

# Third party imports
from flask import Flask, render_template, request, jsonify

# Application imports
from inquisitor import dungeon, core

# Globals
logger = logging.getLogger("inquisitor.app")
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s %(levelname)s:%(filename)s:%(lineno)d] %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

app = Flask(__name__)
dungeon = dungeon.Dungeon("dungeon")
itemsources = core.load_all_sources("sources")


@app.route("/")
def root():
	active_items = dungeon.get_active_items()
	logger.info("Found {} active items".format(len(active_items)))
	for item in active_items:
		item['time_readable'] = str(datetime.fromtimestamp(item['time']))
	active_items.sort(key=lambda i: i['time'])
	return render_template("feed.html", items=active_items[:100])


@app.route("/deactivate/", methods=['POST'])
def deactivate():
	params = request.get_json()
	if 'source' not in params and 'itemid' not in params:
		logger.error("Bad request params: {}".format(params))
	item = dungeon.deactivate_item(params['source'], params['itemid'])
	return jsonify({'active': item['active']})

