import codecs
import os.path
import zipfile

import machine
from res import resolve, Domain


def export_all(dst_path):
    zf_path = os.path.join(dst_path, f'iDSTTVideoMarkerData_{machine.platform_hash_digest}.zip')

    with zipfile.ZipFile(zf_path, 'w') as zf:
        for json_name in os.listdir(resolve(Domain.MARKDATA, make_dirs='self')):
            json_path = resolve(Domain.MARKDATA, json_name)
            with codecs.open(json_path, 'rb') as f_json:
                with zf.open(json_name, 'w') as f_zipped_file:
                    # noinspection PyTypeChecker
                    f_zipped_file.write(f_json.read())


def import_all(zip_path):
    canceled = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            dst_json_path = resolve(Domain.MARKDATA, name, make_dirs='self')
            if os.path.exists(dst_json_path):
                canceled.append(dst_json_path)
                continue
            print(zip_path, name, '->', dst_json_path)
            with zf.open(name, 'r') as f_src:
                with open(dst_json_path, 'wb') as f_dst:
                    f_dst.write(f_src.read())
    return canceled
