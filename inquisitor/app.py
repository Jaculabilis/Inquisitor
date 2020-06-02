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

	return render_template("feed.html", items=active_items[:100])


@app.route("/deactivate/", methods=['POST'])
def deactivate():
	params = request.get_json()
	if 'source' not in params and 'itemid' not in params:
		logger.error("Bad request params: {}".format(params))
	item = loader.WritethroughDict(os.path.join(DUNGEON_PATH, params['source'], params['itemid'] + '.item'))
	item['active'] = False
	return jsonify({'active': item['active']})

