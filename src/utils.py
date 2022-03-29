# -*- coding: utf-8 -*-

import re
from slugify import slugify

re_sanitize_key = re.compile(r"\W")


def sanitize_key(key):
    if isinstance(key, int):
        return str(key)
    else:
        return re_sanitize_key.sub("_", slugify(key, lowercase=False)).strip("_")
