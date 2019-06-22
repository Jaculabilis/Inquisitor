# Standard library imports
import datetime
import logging
import traceback

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


def make_query_link(text, wl, bl):
	wlp = "only=" + ",".join(wl)
	blp = "not="  + ",".join(bl)
	params = [p for p in (wlp, blp) if not p.endswith("=")]
	query = "?{}".format("&".join(params))
	return '<a href="{1}">{0}</a>'.format(text, query)

@app.template_filter("datetimeformat")
def datetimeformat(value, formatstr="%Y-%m-%d %H:%M:%S"):
	if value is None:
		return ""
	dt = datetime.datetime.fromtimestamp(value)
	return dt.strftime(formatstr)

@app.route("/")
def root():
	dungeon = dungeonlib.Dungeon("dungeon")

	# Determine exclusion filters
	filters = []
	wl_param = request.args.get('only')
	wl = wl_param.split(",") if wl_param else []
	bl_param = request.args.get('not')
	bl = bl_param.split(",") if bl_param else []
	if wl:
		filters.append(lambda item: not any([tag in wl for tag in item['tags']]))
	if bl:
		filters.append(lambda item: any([tag in bl for tag in item['tags']]))

	# Get all active+filtered items and all active tags
	total = 0
	active_items = []
	active_tags = set()
	item_read_exceptions = []
	for cell in dungeon:
		for item_id in dungeon[cell]:
			try:
				item = dungeon[cell][item_id]
			except:
				msg = "Exception reading {}/{}".format(cell, item_id)
				logger.error(msg)
				item_read_exceptions.append(msg)
				item_read_exceptions.append(traceback.format_exc())
				continue
			if item['active']:
				active_tags |= set(item['tags'])
				total += 1
				if not any(map(lambda f: f(item), filters)):
					active_items.append(item)
	logger.info("Returning {} of {} items".format(len(active_items), total))
	if item_read_exceptions:
		read_ex = {
			'title': 'Read errors',
			'body': "<pre>{}</pre>".format("\n\n".join(item_read_exceptions)),
			'created': None,
		}
		active_items = [read_ex] + active_items

	if active_items:
		# Create the feed control item
		wl_minus = [make_query_link("only - {}".format(tag), [t for t in wl if t != tag], bl) for tag in wl]
		wl_plus = [make_query_link("only + {}".format(tag), wl + [tag], bl) for tag in active_tags if tag not in wl]
		bl_minus = [make_query_link("not - {}".format(tag), wl, [t for t in bl if t != tag]) for tag in bl]
		bl_plus = [make_query_link("not + {}".format(tag), wl, bl + [tag]) for tag in active_tags if tag not in bl]
		body = "<pre>{}</pre>".format("\n".join(wl_minus + wl_plus + bl_minus + bl_plus))

		feed_control = {
			'title': 'Feed Control',
			'body': body,
			'created': None,
		}
		active_items = [feed_control] + active_items

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

