import json
from typing import Optional

from res import resolve, Domain


class LabelTemplate:
    ROOT_DIR = resolve(Domain.TEMPLATE)

    def __init__(self, json_root):
        self.__json_root = json_root

    @classmethod
    def from_template_name(cls, template_name):
        path = os.path.join(cls.ROOT_DIR, template_name + '.json')
        with open(path, 'r') as f:
            json_root = json.load(f)

        return cls(json_root)

        # TODO: format check
        # dct = {}
        # for k, v in json_root.items():
        #     if not re.fullmatch(r'[0-9]', k):
        #         raise LabelDataFormatError('keys of the root node must be a digit')
        #     if not isinstance(v):

    def iter_labels(self):
        for i, entry in enumerate(self.__json_root):
            name, tags = entry['name'], entry.get('tags', [])
            yield i, name, tags

    def get_label_name_by_index(self, i) -> Optional[str]:
        try:
            return self.__json_root[i]['name']
        except IndexError:
            return None

    def get_entry_by_label_name(self, label_name):
        for i, name, tags in self.iter_labels():
            if name == label_name:
                return dict(
                    name=name,
                    tags=tags
                )
        return None

    def get_tag_by_index(self, label_name, i) -> Optional[str]:
        entry = self.get_entry_by_label_name(label_name)
        if entry is None:
            return None
        try:
            return entry['tags'][i]
        except IndexError:
            return None

    @classmethod
    def list_template_names(cls):
        return [
            os.path.splitext(name)[0]
            for name in os.listdir(cls.ROOT_DIR)
            if name.endswith('.json')
        ]


class LabelDataFormatError(RuntimeError):
    pass
