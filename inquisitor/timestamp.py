import time
import datetime

def now():
	return int(time.time())

def stamp_to_readable(ts, formatstr="%Y-%m-%d %H:%M:%S"):
	dt = datetime.datetime.fromtimestamp(ts)
	return dt.strftime(formatstr)