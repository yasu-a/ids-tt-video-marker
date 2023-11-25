import codecs
import os.path
import zipfile

import machine
from res import resolve, Domain


def export_all(dst_path, exists_ok=False):
    zf_path = os.path.join(dst_path, f'iDSTTVideoMarkerData_{machine.platform_hash_digest}.zip')
    if os.path.exists(zf_path) and not exists_ok:
        return False

    with zipfile.ZipFile(zf_path, 'w') as zf:
        for json_name in os.listdir(resolve(Domain.MARKDATA, make_dirs='self')):
            json_path = resolve(Domain.MARKDATA, json_name)
            with codecs.open(json_path, 'rb') as f_json:
                with zf.open(json_name, 'w') as f_zipped_file:
                    # noinspection PyTypeChecker
                    f_zipped_file.write(f_json.read())

    return True


def import_all(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if not name.endswith('.json'):
                return None
            if '/' in name:
                return None

    canceled = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if not name.endswith('.json'):
                return None
            if '/' in name:
                return None
            dst_json_path = resolve(Domain.MARKDATA, name, make_dirs='parent')
            if os.path.exists(dst_json_path):
                canceled.append(dst_json_path)
                print(zip_path, name, '->', '<canceled>')
                continue
            else:
                print(zip_path, name, '->', dst_json_path)
            with zf.open(name, 'r') as f_src:
                with open(dst_json_path, 'wb') as f_dst:
                    f_dst.write(f_src.read())
    return canceled
