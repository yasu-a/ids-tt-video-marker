import time
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from frozendict import frozendict


def now():
    return time.perf_counter()


@dataclass()
class CacheEntry:
    obj: object
    timestamp: float
    seek_amount: set[int]
    hits: int

    def _score_timestamp(self, now_):
        return (60 - min(60, now_ - self.timestamp)) / 60

    def _score_seek_amount_element(self):
        max_score = 0
        for a in self.seek_amount:
            if max_score > 0 and a == 1:
                max_score = 0
            elif max_score > 1 and a > 2:
                max_score = 1
            elif max_score > 2 and a == -1:
                max_score = 2
            elif max_score > 3 and a < -2:
                max_score = 3
            return max_score / 4

    def _score_hits(self):
        return min(16, self.hits) / 16

    def value(self, now_):
        score = 0
        score += int(self._score_timestamp(now_) * 128)
        score *= 128
        score += int(self._score_hits() * 128)
        score *= 128
        score += int(self._score_seek_amount_element() * 128)
        return score


class CacheKey(NamedTuple):
    args: tuple
    kwargs: frozendict

    @classmethod
    def from_params(cls, args: list | tuple, kwargs: dict):
        return cls(args=tuple(args), kwargs=frozendict(kwargs))

    @property
    def i(self):
        self_, i = self.args
        return i

    def __hash__(self):
        return hash((hash(self.args), hash(self.kwargs)))

    def __lt__(self, other):
        return self.i < other.i


class Cache:
    def __init__(self, f, maxsize):
        self.__f = f
        self.__prev_i = -1
        self.__maxsize = maxsize
        self.__limit_factor = 1.1
        self.__reduction_factor = 0.8
        self.__entries: dict[CacheKey, CacheEntry] = {}

    def set_previous_i(self, i):
        self.__prev_i = i

    def get_seek_amount(self, i):
        return i - self.__prev_i

    def find(self, key):
        return self.__entries.get(key)

    def update_first(self, key, obj):
        entry = CacheEntry(
            obj=obj,
            timestamp=now(),
            seek_amount={self.get_seek_amount(key.i)},
            hits=0
        )
        self.__entries[key] = entry
        return entry.obj

    def update_hit(self, key, entry):
        entry.timestamp = now()
        entry.seek_amount.add(self.get_seek_amount(key.i))
        entry.hits += 1
        return entry.obj

    def pop(self, n):
        sorted_keys = sorted(self.__entries.keys())
        now_ = now()
        values = [self.__entries[k].value(now_) for k in sorted_keys]
        args = np.argsort(values)

        for i in args[:n]:
            self.__entries.pop(sorted_keys[i])

    def ensure_size(self):
        if len(self.__entries) > int(self.__maxsize * self.__limit_factor):
            self.pop(len(self.__entries) - int(self.__maxsize * self.__reduction_factor))

    def __call__(self, *args, **kwargs):
        key = CacheKey.from_params(args=args, kwargs=kwargs)
        entry = self.find(key)
        if entry is None:
            obj = self.__f(*args, **kwargs)
            result = self.update_first(key, obj)
        else:
            result = self.update_hit(key, entry)
        self.set_previous_i(key.i)
        self.ensure_size()
        return result


def lru_cache(maxsize):
    print(maxsize)

    def decorator(f):
        cache = Cache(f, maxsize)

        def wrapper(self_, i):
            return cache(self_, i)

        return wrapper

    return decorator
