import os
import logging


# Constants governing config resolution:
# Path to the config file, containing key-value pairs of the other settings
CONFIG_ENVVAR = 'INQUISITOR_CONFIG'
DEFAULT_CONFIG_PATH = '/etc/inquisitor.conf'

# Path to the folder where items are stored
CONFIG_DATA = 'DataPath'
DEFAULT_DATA_PATH = '/var/inquisitor/data/'

# Path to the folder where source modules are stored
CONFIG_SOURCES = 'SourcePath'
DEFAULT_SOURCES_PATH = '/var/inquisitor/sources/'

# Path to the folder where cached files are stored
CONFIG_CACHE = 'CachePath'
DEFAULT_CACHE_PATH = '/var/inquisitor/cache/'

# Path to a log file where logging will be redirected
CONFIG_LOGFILE = 'LogFile'
DEFAULT_LOG_FILE = None

# Whether logging is verbose
CONFIG_VERBOSE = 'Verbose'
DEFAULT_VERBOSITY = 'false'

# Subfeed source lists, with each subfeed config separated by lines and
# sources within a subfeed separated by spaces
CONFIG_SUBFEEDS = 'Subfeeds'
DEFAULT_SUBFEEDS = None
SUBFEED_CONFIG_FILE = 'subfeeds.conf'


def read_config_file(config_path):
	"""
	Reads a config file of key-value pairs, where non-blank lines are
	either comments beginning with the character '#' or keys and values
	separated by the character '='.
	"""
	# Parse the config file into key-value pairs
	if not os.path.isfile(config_path):

		raise FileNotFoundError(f'No config file found at {config_path}, try setting {CONFIG_ENVVAR}')
	accumulated_configs = {}
	current_key = None
	with open(config_path, 'r', encoding='utf8') as cfg:
		line_no = 0
		for line in cfg:
			line_no += 1
			# Skip blank lines and comments
			if not line.strip() or line.lstrip().startswith('#'):
				continue
			# Accumulate config keyvalue pairs
			if '=' in line:
				# "key = value" begins a new keyvalue pair
				current_key, value = line.split('=', maxsplit=1)
				current_key = current_key.strip()
				accumulated_configs[current_key] = value.strip()
			else:
				# If there's no '=' and no previous key, throw
				if not current_key:
					raise ValueError(f'Invalid config format on line {line_no}')
				else:
					accumulated_configs[current_key] += '\n' + line.strip()

	return accumulated_configs


def parse_subfeed_value(value):
	sf_defs = [sf.strip() for sf in value.split('\n') if sf.strip()]
	subfeeds = {}
	for sf_def in sf_defs:
		if ':' not in sf_def:
			raise ValueError(f'Invalid subfeed definition: {sf_def}')
		sf_name, sf_sources = sf_def.split(':', maxsplit=1)
		sf_sources = sf_sources.split()
		subfeeds[sf_name.strip()] = [source.strip() for source in sf_sources]
	return subfeeds


# Read envvar for config file location, with fallback to default
config_path = os.path.abspath(
	os.environ.get(CONFIG_ENVVAR) or
	DEFAULT_CONFIG_PATH
)

configs = read_config_file(config_path)

# Extract and validate config values
data_path = configs.get(CONFIG_DATA) or DEFAULT_DATA_PATH
if not os.path.isabs(data_path):
	raise ValueError(f'Non-absolute data path: {data_path}')
if not os.path.isdir(data_path):
	raise FileNotFoundError(f'Cannot find directory {data_path}')

source_path = configs.get(CONFIG_SOURCES) or DEFAULT_SOURCES_PATH
if not os.path.isabs(source_path):
	raise ValueError(f'Non-absolute source path: {source_path}')
if not os.path.isdir(source_path):
	raise FileNotFoundError(f'Cannot find directory {source_path}')

cache_path = configs.get(CONFIG_CACHE) or DEFAULT_CACHE_PATH
if not os.path.isabs(cache_path):
	raise ValueError(f'Non-absolute cache path: {cache_path}')
if not os.path.isdir(cache_path):
	raise FileNotFoundError(f'Cannot find directory {cache_path}')

log_file = configs.get(CONFIG_LOGFILE) or DEFAULT_LOG_FILE
if log_file and not os.path.isabs(log_file):
	raise ValueError(f'Non-absolute log file path: {log_file}')

is_verbose = configs.get(CONFIG_VERBOSE) or DEFAULT_VERBOSITY
if is_verbose != 'true' and is_verbose != 'false':
	raise ValueError(f'Invalid verbose value (must be "true" or "false"): {is_verbose}')
is_verbose = (is_verbose == 'true')

subfeeds = configs.get(CONFIG_SUBFEEDS) or DEFAULT_SUBFEEDS
if subfeeds:
	subfeeds = parse_subfeed_value(subfeeds)


def get_subfeed_overrides():
	"""
	Check for and parse the secondary subfeed configuration file
	"""
	path = os.path.join(source_path, SUBFEED_CONFIG_FILE)
	if not os.path.isfile(path):
		return None
	overrides = read_config_file(path)
	if CONFIG_SUBFEEDS not in overrides:
		return None
	value = overrides[CONFIG_SUBFEEDS]
	if not value:
		return None
	parsed_value = parse_subfeed_value(value)
	return parsed_value


# Set up logging
logger = logging.getLogger("inquisitor")
logger.setLevel(logging.DEBUG)

def add_logging_handler(verbose, log_filename):
	"""
	Adds a logging handler according to the given settings
	"""
	log_format = (
		'[{asctime}] [{levelname}:{filename}:{lineno}] {message}'
		if verbose else
		'[{levelname}] {message}'
	)
	formatter = logging.Formatter(log_format, style='{')

	log_level = (
		logging.DEBUG
		if verbose else
		logging.INFO
	)
	handler = (
		logging.handlers.RotatingFileHandler(
			log_filename,
			encoding='utf8',
			maxBytes=2**22, # 4 MB per log file
			backupCount=4)  # 16 MB total
		if log_filename else
		logging.StreamHandler()
	)
	handler.setFormatter(formatter)
	handler.setLevel(log_level)

	logger.addHandler(handler)

def init_default_logging():
	add_logging_handler(is_verbose, log_file)
