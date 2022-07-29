from __future__ import print_function

from random import randint
from timeit import timeit
import profile

from veb import vEBTree


def random_tree(size):
    tree = vEBTree.of_size(size)
    for _ in range(randint(0, tree.universe_size - 1)):
        tree.add(randint(0, tree.universe_size - 1))
    return tree


for size in range(1, 16):
    bench = "random_tree(2 ** {0})".format(size)
    t = timeit(bench, "from __main__ import random_tree, size, vEBTree", number=1000)
    print(bench, ":", t)
