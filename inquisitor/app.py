# Standard library imports
import os
import traceback

# Third party imports
from flask import Flask, render_template, request, jsonify

# Application imports
from configs import logger, DUNGEON_PATH
import loader
import timestamp

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
	active_tags = set()
	for item in items:
			if item['active']:
				active_tags |= set(item['tags'])
				total += 1
				if not any(map(lambda f: f(item), filters)):
					active_items.append(item)
	# Sort items by time
	active_items.sort(key=lambda i: i['time'] if 'time' in i and i['time'] else 0)

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
		wl_minus = [make_query_link("only - {}".format(tag), [t for t in wl if t != tag], bl) for tag in wl]
		wl_plus = [make_query_link("only + {}".format(tag), wl + [tag], bl) for tag in active_tags if tag not in wl]
		bl_minus = [make_query_link("not - {}".format(tag), wl, [t for t in bl if t != tag]) for tag in bl]
		bl_plus = [make_query_link("not + {}".format(tag), wl, bl + [tag]) for tag in active_tags if tag not in bl]
		body = "<pre>{}</pre>".format("\n".join(wl_minus + wl_plus + bl_minus + bl_plus))

		feed_control = {
			'title': 'Feed Control [{}]'.format(total),
			'body': body,
			'created': None,
		}
		active_items.insert(0, feed_control)

	return render_template("feed.html", items=active_items[:100])


@app.route("/deactivate/", methods=['POST'])
def deactivate():
	params = request.get_json()
	if 'source' not in params and 'itemid' not in params:
		logger.error("Bad request params: {}".format(params))
	item = loader.WritethroughDict(os.path.join(DUNGEON_PATH, params['source'], params['itemid'] + '.item'))
	item['active'] = False
	return jsonify({'active': item['active']})

