import codecs
import datetime
import json
import os

from res import resolve, Domain


def take(src_json_path, src_json_root):
    _, src_json_name = os.path.split(src_json_path)
    now = datetime.datetime.now()
    dst_json_name = f'{os.path.splitext(src_json_name)[0]} {now.strftime("%Y%m%d_%H%M%S_%f")}.json'
    dst_json_path = resolve(
        Domain.MARKDATA_BACKUP,
        now.strftime('%Y%m%d'),
        dst_json_name,
        make_dirs='parent'
    )

    with codecs.open(dst_json_path, 'w', encoding='utf-8') as f:
        json.dump(src_json_root, f, indent=2, sort_keys=True, ensure_ascii=False)
