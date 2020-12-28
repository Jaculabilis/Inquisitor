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
DEFAULT_VERBOSITY = False


def read_config_file(config_path):
	"""
	Reads a config file of key-value pairs, where non-blank lines are
	either comments beginning with the character '#' or keys and values
	separated by the character '='.
	"""
	# Parse the config file into key-value pairs
	if not os.path.isfile(config_path):
		raise FileNotFoundError(f'No config file found at {config_path}')
	accumulated_configs = {}
	with open(config_path, 'r', encoding='utf8') as cfg:
		line_no = 0
		for line in cfg:
			line_no += 1
			# Skip blank lines
			if not line.strip():
				continue
			# Skip comments
			if line.lstrip().startswith('#'):
				continue
			# Accumulate config keyvalue pairs
			if '=' not in line:
				raise ValueError(f'Invalid config format on line {line_no}')
			key, value = line.split('=', maxsplit=1)
			accumulated_configs[key.strip()] = value.strip()

	return accumulated_configs


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

is_verbose = (configs.get(CONFIG_VERBOSE) == 'true') or DEFAULT_VERBOSITY


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
		logging.FileHandler(log_filename, encoding='utf8')
		if log_filename else
		logging.StreamHandler()
	)
	handler.setFormatter(formatter)
	handler.setLevel(log_level)

	logger.addHandler(handler)

def init_default_logging():
	add_logging_handler(is_verbose, log_file)
