import sys
from enum import Enum

DEBUG = False if 'disable_debug' in sys.argv else True

print(f'{DEBUG=}')


class FrameAction(Enum):
    FIRST_PAGE = ('#first', 'seek')
    LAST_PAGE = ('#last', 'seek')
    NEXT_PAGE = (+1, 'relative', 'seek')
    PREV_PAGE = (-1, 'relative', 'seek')
    NEXT_PAGE_STRIDES = ('#fps', +0.2, 'relative', 'seek')
    PREV_PAGE_STRIDES = ('#fps', -0.2, 'relative', 'seek')
    NEXT_PAGE_SECONDS = ('#fps', +10, 'relative', 'seek')
    PREV_PAGE_SECONDS = ('#fps', -10, 'relative', 'seek')
    NEXT_MARKER = (0, 'relative', 'marked_after', '$LAST_PAGE', 'seek')
    PREV_MARKER = (0, 'relative', 'marked_before', '$FIRST_PAGE', 'seek')

    def parse_request_absolute(self, i_current, n_frames, fps, mark_getter):
        constants = {
            'fps': fps,
            'first': 0,
            'last': n_frames - 1
        }
        acc = None
        for inst in self.value:
            if isinstance(inst, (int, float)):
                num = inst
            elif inst.startswith('#'):
                num = constants.get(inst[1:])
                num = int(round(num, 0))
            else:
                num = None

            if isinstance(inst, str) \
                    and inst.startswith('$') \
                    and inst[1:] in type(self).__members__:
                inst = type(self).__members__[inst[1:]]
                if acc is None:
                    return inst.parse_request_absolute(i_current, n_frames, fps, mark_getter)
            elif acc is None:
                acc = num
            elif num is not None:
                acc = int(acc * num)
            elif inst == 'relative':
                acc = i_current + acc
            elif inst == 'marked_after':
                acc = mark_getter(acc, +1)
            elif inst == 'marked_before':
                acc = mark_getter(acc, -1)
            elif inst == 'seek':
                assert acc is not None, (self, self.value, inst, acc)
                return acc
            else:
                assert False, (self, self.value, inst, acc)

        assert False, (self, self.value, '<EOL>', acc)
