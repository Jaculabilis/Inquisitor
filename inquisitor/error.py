import os
import logging
import json
import random

from inquisitor import timestamp
from inquisitor.configs import DUNGEON_PATH, logger

logger = logging.getLogger("inquisitor")


def as_item(title, body=None):
    iid = "{:x}".format(random.getrandbits(16 * 4))
    item = {
        "id": iid,
        "source": "inquisitor",
        "title": title,
        "active": True,
        "created": timestamp.now(),
        "tags": ["inquisitor", "error"],
    }
    if body is not None:
        item["body"] = "<pre>{}</pre>".format(body)
    path = os.path.join(DUNGEON_PATH, "inquisitor", iid + ".item")
    logger.error(json.dumps(item))
    with open(path, "w") as f:
        f.write(json.dumps(item, indent=2))
