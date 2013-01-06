"""
Dynamically allocated van Emde Boas Trees (Queues).

"""

from __future__ import division
from collections import defaultdict

try:
    from collections.abc import MutableSet
except ImportError:
    from collections import MutableSet

try:
    from math import ceil, floor, log2
except ImportError:
    from math import log
    def log2(n): return log(n, 2)

if not isinstance(ceil(1.0), int):
    _ceil, _floor = ceil, floor
    def ceil(n): return int(_ceil(n))
    def floor(n): return int(_floor(n))


__version__ = "0.1.0"


class _EmptyVEBTree(object):
    min = max = None
    universe_size = 0
    def __contains__(self, i): return False
    def __iter__(self): return iter([])
    def __len__(self): return 0
    def predecessor(self, i): return None
    def successor(self, i): return None
    def discard(self, i): return None


_EMPTY = _EmptyVEBTree()


class vEBTree(MutableSet):

    _root = _EMPTY
    universe_size = _root.universe_size
    discard = _root.discard
    predecessor = _root.predecessor
    successor = _root.successor

    def __init__(self, contents=()):
        if contents:
            self.update(contents)

    def __bool__(self):
        return self.min is not None
    __nonzero__ = __bool__

    def __contains__(self, i):
        return i in self._root

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        return (
            self.universe_size == other.universe_size and
            self.min == other.min and
            self.max == other.max and
            len(self) == len(other) and
            all(i == j for i, j in zip(self, other))
        )

    def __iter__(self):
        return iter(self._root)

    def __len__(self):
        return len(self._root)

    def __repr__(self):
        return "vEBTree(%r)" % list(self)

    def _update_root(self, new_root):
        self._root = new_root
        self.universe_size = new_root.universe_size
        self.discard = new_root.discard
        self.predecessor = new_root.predecessor
        self.successor = new_root.successor

    @classmethod
    def of_size(cls, n):
        tree = cls()
        tree.grow(n)
        return tree

    @property
    def min(self):
        return self._root.min

    @property
    def max(self):
        return self._root.max

    def grow(self, to_size):
        if to_size <= self.universe_size:
            return
        if to_size <= 2:
            return self._update_root(_vEBLeaf())

        square_root = ceil(log2(to_size))
        old_root = self._root
        self._update_root(_vEBTree(1 << square_root))

        if old_root is not _EMPTY:
            if log2(square_root).is_integer():  # an even power of two
                # XXX: I *think* there's a bug here with no failing test. We
                # should have to update something in the new root's summary.
                self._root.clusters[0] = old_root
            else:
                self.update(old_root)           # odd, need to redistribute

    def add(self, i):
        if i >= self.universe_size:
            self.grow(i + 1)
        self._root.add(i)

    def update(self, iterable):
        for i in iterable:
            self.add(i)


class _vEBLeaf(object):
    universe_size = 2

    def __init__(self):
        self.values = [False, False]

    def __contains__(self, x):
        if x > 2:
            return False
        return self.values[x]

    def __iter__(self):
        return (i for i, v in enumerate(self.values) if v)

    def __len__(self):
        return self.values.count(True)

    def __reversed__(self):
        return (i for i, v in zip((1, 0), reversed(self.values)) if v)

    @property
    def min(self):
        return next(iter(self), None)

    @property
    def max(self):
        return next(reversed(self), None)

    def add(self, x):
        self.values[x] = True

    def discard(self, x):
        self.values[x] = False

    def predecessor(self, x):
        if x < 1:
            return
        elif x == 1:
            return 0 if self.values[0] else None
        else:
            return 1 if self.values[1] else 0 if self.values[0] else None

    def successor(self, x):
        if x > 0:
            return
        elif x == 0:
            return 1 if self.values[1] else None
        else:
            return 0 if self.values[0] else 1 if self.values[1] else None


class _vEBTree(object):

    min = max = None

    def __init__(self, n):
        root = ceil(log2(n)) / 2
        upper, self._lower = 1 << ceil(root), 1 << floor(root)
        self.summary = vEBTree.of_size(upper)
        self.clusters = [None] * upper
        self.universe_size = n

    def __contains__(self, x):
        if self.min is None:
            return False
        elif x == self.min:
            return True

        high, low = divmod(x, self._lower)
        if self.clusters[high] is None:
            return False
        return low in self.clusters[high]

    def __iter__(self):
        i, _ = minimum, maximum = self.min, self.max

        if minimum is None:
            return
        yield minimum

        while i != maximum:
            i = self.successor(i)
            yield i

    def __reversed__(self):
        _, i = minimum, maximum = self.min, self.max

        if minimum is None:
            return
        yield maximum

        while i != minimum:
            i = self.predecessor(i)
            yield i

    def __len__(self):
        return sum(1 for _ in self)

    def add(self, x):
        if self.min is None:
            self.min = self.max = x
            return

        if x == self.min:
            return
        if x < self.min:
            x, self.min = self.min, x
        if x > self.max:
            self.max = x

        high, low = divmod(x, self._lower)
        cluster = self.clusters[high]

        if cluster is None:
            cluster = self.clusters[high] = vEBTree.of_size(self.summary.universe_size)
            self.summary.add(high)
        cluster.add(low)

    def discard(self, x):
        if self.min is None or x < self.min:
            return

        if x == self.min:
            new_min_in = self.summary.min
            if new_min_in is None:
                self.min = self.max = None
            else:
                cluster = self.clusters[new_min_in]
                new_min = cluster.min
                x = self.min = new_min_in * self._lower + new_min
                # XXX: I don't know why just changing to 
                # cluster.discard(new_min_in) and returning doesn't work here

        high, low = divmod(x, self._lower)
        cluster = self.clusters[high]

        if cluster is None:
            return
        cluster.discard(low)

        if cluster.min is None:
            self.clusters[high] = None
            self.summary.discard(high)

        if x == self.max:
            global_max = self.summary.max
            if global_max is None:
                self.max = self.min
            else:
                self.max = global_max * self._lower + self.clusters[global_max].max

    def predecessor(self, x):
        if self.min is None or x <= self.min:
            return None
        elif x > self.max:
            return self.max

        high, low = divmod(x, self._lower)
        cluster = self.clusters[high]

        if cluster is None or low <= cluster.min:
            high = self.summary.predecessor(high)
            if high is None:
                return self.min
            return high * self._lower + self.clusters[high].max
        else:
            low = cluster.predecessor(low)
            return high * self._lower + low

    def successor(self, x):
        if self.min is None or x >= self.max:
            return None
        elif x < self.min:
            return self.min

        high, low = divmod(x, self._lower)
        cluster = self.clusters[high]

        if cluster is None or low >= cluster.max:
            high = self.summary.successor(high)
            return high * self._lower + self.clusters[high].min
        else:
            low = cluster.successor(low)
            return high * self._lower + low
