# Standard library imports
from datetime import datetime
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


@app.route("/")
def root():
	dungeon = dungeonlib.Dungeon("dungeon")
	active_items = []
	for cell in dungeon:
		for item_id in dungeon[cell]:
			try:
				item = dungeon[cell][item_id]
				if item['active']:
					active_items.append(item)
			except:
				logger.error("Exception reading {}/{}".format(cell, item_id))
	logger.info("Found {} active items".format(len(active_items)))
	return render_template("feed.html", items=active_items[:100])


@app.route("/deactivate/", methods=['POST'])
def deactivate():
	dungeon = dungeonlib.Dungeon("dungeon")
	params = request.get_json()
	if 'source' not in params and 'itemid' not in params:
		logger.error("Bad request params: {}".format(params))
	item = dungeon[params['source']][params['itemid']]
	item.deactivate()
	return jsonify({'active': item['active']})

