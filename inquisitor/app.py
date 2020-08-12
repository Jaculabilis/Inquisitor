# Standard library imports
from datetime import datetime, timedelta
import os
import traceback

# Third party imports
from flask import Flask, render_template, request, jsonify, abort

# Application imports
from inquisitor.configs import logger, DUNGEON_PATH, CACHE_PATH
from inquisitor import sources, loader, timestamp

# Globals
app = Flask(__name__)


def make_query_link(text, wl, bl):
	wlp = "only=" + ",".join(wl)
	blp = "not="  + ",".join(bl)
	params = [p for p in (wlp, blp) if not p.endswith("=")]
	query = "?{}".format("&".join(params))
	return '<a href="{1}">{0}</a>'.format(text, query)

@app.template_filter("datetimeformat")
def datetimeformat(value):
	return timestamp.stamp_to_readable(value) if value is not None else ""

@app.route("/")
def root():
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
	items, errors = loader.load_active_items()
	active_items = []
	active_tags = {}
	for item in items:
		if item['active']:
			for tag in item['tags']:
				if tag not in active_tags: active_tags[tag] = 0
				active_tags[tag] += 1
			# active_tags |= set(item['tags'])
			total += 1
			if not any(map(lambda f: f(item), filters)):
				active_items.append(item)
	# Sort items by time
	active_items.sort(key=lambda i: i['time'] if 'time' in i and i['time'] else i['created'] if 'created' in i and i['created'] else 0)

	logger.info("Returning {} of {} items".format(len(active_items), total))
	if errors:
		read_ex = {
			'title': 'Read errors',
			'body': "<pre>{}</pre>".format("\n\n".join(errors)),
			'created': None,
		}
		active_items.insert(0, read_ex)

	if total > 0:
		# Create the feed control item
		link_table = ["<tr><td>{0}</td><td>{1}</td><td></td><td></td></tr>".format(
			total, make_query_link("all", [], []))]
		for tag, count in sorted(active_tags.items(), key=lambda i: i[0].lower()):
			links = [count]
			links.append(make_query_link(tag, [tag], []))
			if tag in wl:
				new_wl = [t for t in wl if t != tag]
				links.append(make_query_link("-only", new_wl, bl))
			else:
				new_bl = [t for t in bl if t != tag]
				links.append(make_query_link("+only", wl + [tag], new_bl))
			if tag in bl:
				new_bl = [t for t in bl if t != tag]
				links.append(make_query_link("-not", wl, new_bl))
			else:
				new_wl = [t for t in wl if t != tag]
				links.append(make_query_link("+not", new_wl, bl + [tag]))
			link_table.append("<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td></tr>".format(*links))
		body = '<table class="feed-control">{}</table>'.format("\n".join(link_table))

		feed_control = {
			'title': 'Feed Control [{}/{}]'.format(len(active_items), total),
			'body': body,
		}
		active_items.insert(0, feed_control)

	selection = active_items[:100]

	return render_template("feed.html",
		items=selection,
		mdeac=[
			{'source': item['source'], 'itemid': item['id']}
			for item in selection
			if 'id' in item])

@app.route("/deactivate/", methods=['POST'])
def deactivate():
	params = request.get_json()
	if 'source' not in params and 'itemid' not in params:
		logger.error("Bad request params: {}".format(params))
	item = loader.load_item(params['source'], params['itemid'])
	if item['active']:
		logger.debug(f"Deactivating {params['source']}/{params['itemid']}")
	item['active'] = False
	return jsonify({'active': item['active']})

@app.route("/punt/", methods=['POST'])
def punt():
	params = request.get_json()
	if 'source' not in params and 'itemid' not in params:
		logger.error("Bad request params: {}".format(params))
	item = loader.load_item(params['source'], params['itemid'])
	tomorrow = datetime.now() + timedelta(days=1)
	morning = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 6, 0, 0)
	til_then = morning.timestamp() - item['created']
	item['tts'] = til_then
	return jsonify(item.item)

@app.route("/mass-deactivate/", methods=['POST'])
def mass_deactivate():
	params = request.get_json()
	if 'items' not in params:
		logger.error("Bad request params: {}".format(params))
	for info in params.get('items', []):
		source = info['source']
		itemid = info['itemid']
		item = loader.load_item(source, itemid)
		if item['active']:
			logger.debug(f"Deactivating {info['source']}/{info['itemid']}")
		item['active'] = False
	return jsonify({})

@app.route("/callback/", methods=['POST'])
def callback():
	params = request.get_json()
	if 'source' not in params and 'itemid' not in params:
		logger.error("Bad request params: {}".format(params))
	sources.item_callback(params['source'], params['itemid'])
	return jsonify({})

@app.route('/cache/<path:cache_path>')
def cache(cache_path):
	path = os.path.join(CACHE_PATH, cache_path)
	if not os.path.isfile(path):
		return abort(404)
	with open(path, 'rb') as f:
		return f.read()
