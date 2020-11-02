import iso8601
import re
from datetime import datetime


def cast_date(ts):
    if ts is not None:
        return iso8601.parse_date(ts)
    return ts


def extract_id(x):
    if x is not None:
        regx = "id=(\d+)"
        return re.search(regx, x).group(1)
    return x


def parse_bounds(obj):
    return obj.get("lower_bound", None), obj.get("upper_bound", None)


def parse_distr(obj, key):
    keys = ["percentage", "age", "gender"]
    if key == "reg":
        keys = ["percentage", "region"]
    if obj is not None and sum([1 for k in keys if k in obj.keys()]) == len(keys):
        return [obj[k] for k in keys]
    return [None for k in keys]
