import collections
from typing import Optional, NamedTuple

import numpy as np
from PyQt5.QtWidgets import QLabel
from frozendict import frozendict


class LayeredTUILabel(QLabel):

    def __init__(self, *__args):
        super().__init__(*__args)

        # noinspection PyUnresolvedReferences
        self.setStyleSheet(
            'background-color: white; '
            'color: white; '
            'font-size: 3; '
            'font-weight: 600;'
        )

        self.__width = None
        self.__layers: collections.OrderedDict[int, Optional[RichText]] \
            = collections.OrderedDict()

    def setText(self, *args):
        raise ValueError('Unsupported operation')

    def tui_clear(self, width: int):
        self.__width = width
        self.__layers = collections.OrderedDict()

    def tui_write(self, i: int, text: str, **kwargs):
        if 'color' not in kwargs:
            kwargs['color'] = 'black'
        component = RichText(text=text, **kwargs)
        self.__layers[i] = component

    def tui_move_to_top(self, i: int):
        try:
            rt = self.__layers.pop(i)
        except KeyError:
            pass
        else:
            self.__layers[i] = rt

    def tui_commit(self):
        chars = [RichText(text='_')] * self.__width

        for i, rt in self.__layers.items():
            for j, rt_char in enumerate(rt.iter_each_char()):
                if i + j >= len(chars):
                    continue
                chars[i + j] = rt_char
        text = RichText.array_to_html(chars)
        super().setText(text)


class RichText(NamedTuple):
    text: str
    color: Optional[str] = None
    background: Optional[str] = None

    def iter_each_char(self):
        fields = self._asdict()
        for ch in self.text:
            yield RichText(**(fields | dict(text=ch)))

    def format(self, text=None):
        text = text or self.text
        if self.color:
            text = f'<font color={self.color!r}>{text}</font>'
        if self.background:
            text = f'<span style="background-color: {self.background}">{text}</span>'
        return text

    def __decoration_hash(self):
        decoration_field_names = set(self._fields) - {'text'}
        decoration_fields = frozendict(
            (field_names, getattr(self, field_names))
            for field_names in decoration_field_names
        )
        return hash(decoration_fields)

    @classmethod
    def array_to_html(cls, rts: list['RichText']):
        ha = np.array([rt.__decoration_hash() for rt in rts])
        ha_change = ha[1:] != ha[:-1]

        lst = []
        for i in range(len(rts)):
            if i == 0 or ha_change[i - 1]:
                lst.append([])
            lst[-1].append(rts[i])

        body = ''.join(
            rt_lst[0].format(
                text=''.join(
                    rt.text for rt in rt_lst
                )
            ) for rt_lst in lst
        )

        html = f'<html>{body}</html>'

        return html
