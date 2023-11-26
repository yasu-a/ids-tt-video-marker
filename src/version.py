import codecs
import datetime
import json
import os.path
import re
import time
import urllib.request
from pprint import pprint

from res import resolve, Domain

CHECK_UPDATE = True

_APP_INFO_JSON_PATH = resolve(Domain.APPINFO, 'appinfo.json', make_dirs='parent')
_GITHUB_VERSIONS_URL = 'https://api.github.com/repos/yasu-a/ids-tt-video-marker/branches'
_GITHUB_BRANCH_URL_FORMAT = 'https://github.com/yasu-a/ids-tt-video-marker/tree/{branch_name}'

with open(_APP_INFO_JSON_PATH, 'r') as f:
    app_info = json.load(f)

_RETRIEVE_TIME_SPAN = datetime.timedelta(hours=2)


def retrieve_branches_json():
    cache_path = resolve(Domain.APPINFO, 'branches_cache.json', make_dirs='parent')
    cache = None
    if os.path.exists(cache_path):
        with codecs.open(cache_path, 'r', encoding='utf-8') as f:
            cache_raw = json.load(f)
            timestamp = datetime.datetime.fromtimestamp(cache_raw['timestamp'])
            if datetime.datetime.now() - timestamp <= _RETRIEVE_TIME_SPAN:
                cache = cache_raw['main']

    if cache is not None:
        print('Retrieved branches from cache')
        return cache

    print(f'urllib.request.urlopen({_GITHUB_VERSIONS_URL})')
    with urllib.request.urlopen(_GITHUB_VERSIONS_URL) as res:
        branches_json = json.loads(res.read())
    with codecs.open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(
            dict(
                timestamp=int(time.time()),
                main=branches_json
            ),
            f
        )
    print('Retrieved branches from github')
    return branches_json


def version_to_order(major_, minor_):
    return major_ * 100 + minor_


app_version_str = f"{app_info['version']['major']}.{app_info['version']['minor']}"
app_version_int = version_to_order(app_info['version']['major'], app_info['version']['minor'])

if CHECK_UPDATE:
    _branches_json = retrieve_branches_json()

    versions = {}
    for branch_dct in _branches_json:
        branch_name = branch_dct['name']
        m = re.fullmatch(r'release/stable/(\d+)\.(\d+)', branch_name)
        if not m:
            continue
        major, minor = map(int, m.groups())
        versions[f'{major}.{minor}'] = dict(
            url=_GITHUB_BRANCH_URL_FORMAT.format(branch_name=branch_name),
            order=version_to_order(major, minor)
        )

    latest_version, latest_version_info \
        = sorted(versions.items(), key=lambda item: item[1]['order'])[-1]

    update_available = latest_version_info['order'] > app_version_int
else:
    versions = {}
    latest_version, latest_version_info = None, None
    update_available = None

    print('UPDATE UNCHECKED!!!!')

pprint(versions)
print(f'{latest_version=}')
print(f'{latest_version_info=}')
