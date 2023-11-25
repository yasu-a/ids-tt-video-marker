import json
import re
import urllib.request
from pprint import pprint

_APP_INFO_JSON_PATH = 'app_info.json'
_GITHUB_VERSIONS_URL = 'https://api.github.com/repos/yasu-a/ids-tt-video-marker/branches'
_GITHUB_BRANCH_URL_FORMAT = 'https://github.com/yasu-a/ids-tt-video-marker/tree/{branch_name}'

with open(_APP_INFO_JSON_PATH, 'r') as f:
    app_info = json.load(f)

with urllib.request.urlopen(_GITHUB_VERSIONS_URL) as res:
    _branches_json = json.loads(res.read())


def version_to_order(major_, minor_):
    return major_ * 100 + minor_


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

pprint(versions)
print(f'{latest_version=}')
print(f'{latest_version_info=}')

app_version_str = f"{app_info['version']['major']}.{app_info['version']['minor']}"
app_version_int = version_to_order(app_info['version']['major'], app_info['version']['minor'])
update_available = latest_version_info['order'] > app_version_int
