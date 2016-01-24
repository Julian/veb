from unittest import TestCase, expectedFailure
import bisect
import random

from veb import vEBTree


class VEBTestMixin(object):
    def test_repr(self):
        self.assertEqual(repr(self.t), "vEBTree(%r)" % list(self.t))

    def test_len(self):
        self.assertEqual(len(self.t), 0)

        self.t.add(0)
        self.assertEqual(len(self.t), 1)

        self.t.add(1)
        self.assertEqual(len(self.t), 2)

    def test_it_is_empty_when_created(self):
        for i in range(self.t.universe_size):
            self.assertNotIn(i, self.t)

        self.assertEqual(list(self.t), [])

    def test_iter_returns_contained_elements(self):
        evens = range(self.t.universe_size, 0, 2)
        for i in evens:
            self.t.add(i)
        self.assertEqual(list(self.t), list(evens))

    def test_bool_returns_whether_empty(self):
        self.assertFalse(self.t)
        self.t.add(0)
        self.assertTrue(self.t)

    def test_out_of_bounds_containment_is_false(self):
        self.assertNotIn(self.t.universe_size + 1, self.t)

    def test_add_twice_does_nothing(self):
        self.t.add(0)
        self.t.add(0)
        self.assertIn(0, self.t)

    def test_discard_not_present_does_nothing(self):
        self.t.discard(0)
        self.t.discard(0)
        self.assertNotIn(0, self.t)

    def test_negatives(self):
        self.t.update([0, 1])
        self.assertEqual(self.t.successor(-1), 0)
        self.assertEqual(self.t.predecessor(self.t.universe_size + 1), 1)


class TestVEBTree(TestCase, VEBTestMixin):
    def setUp(self):
        self.t = vEBTree.of_size(4)

    def test_add_to_empty(self):
        self.t.add(3)
        self.assertNotIn(0, self.t)
        self.assertNotIn(1, self.t)
        self.assertNotIn(2, self.t)
        self.assertIn(3, self.t)

        self.assertEqual(self.t.min, 3)

    def test_add_min(self):
        self.t.add(0)
        self.assertIn(0, self.t)

        self.t.add(0)
        self.assertIn(0, self.t)

    def test_add_less_than_min(self):
        self.t.add(1)
        self.t.add(0)
        self.assertIn(0, self.t)
        self.assertIn(1, self.t)

        self.assertEqual(self.t.min, 0)

    def test_add_greater_than_max(self):
        self.t.add(0)
        self.t.add(1)
        self.assertIn(0, self.t)
        self.assertIn(1, self.t)

        self.assertEqual(self.t.max, 1)

    def test_discard_less_than_min(self):
        self.t.add(1)
        self.t.discard(0)
        self.assertNotIn(0, self.t)

        self.assertEqual(self.t.min, 1)

    def test_discard_min_last_element(self):
        self.t.add(1)
        self.t.discard(1)
        self.assertNotIn(1, self.t)
        self.assertIsNone(self.t.min)
        self.assertIsNone(self.t.max)

    def test_discard_min_update_to_new_min(self):
        self.t.update([0, 1])
        self.t.discard(0)
        self.assertNotIn(0, self.t)
        self.assertEqual(self.t.min, 1)
        self.assertEqual(self.t.max, 1)

    def test_predecessor_empty(self):
        self.assertIsNone(self.t.predecessor(2))

    def test_predecessor_greater_than_max(self):
        self.t.add(2)
        self.assertEqual(self.t.predecessor(3), 2)

    def test_predecessor_min_or_smaller(self):
        self.t.add(3)
        self.assertEqual(self.t.min, 3)
        self.assertIsNone(self.t.predecessor(3))

    def test_predecessor_in_current_cluster(self):
        self.t.update([0, 3])
        self.assertEqual(self.t.predecessor(1), 0)

    def test_predecessor_in_next_cluster_current_cluster_only_has_min(self):
        self.t.update([0, 3])
        self.assertEqual(self.t.predecessor(2), 0)

    def test_predecessor_in_next_cluster_current_cluster_has_elements(self):
        self.t.update([0, 2, 3])
        self.assertEqual(self.t.predecessor(2), 0)

    def test_successor_empty(self):
        self.assertIsNone(self.t.successor(2))

    def test_successor_less_than_min(self):
        self.t.add(3)
        self.assertEqual(self.t.successor(2), 3)

    def test_successor_max_or_bigger(self):
        self.t.add(3)
        self.assertEqual(self.t.max, 3)
        self.assertIsNone(self.t.successor(3))

    def test_successor_in_current_cluster(self):
        self.t.update([1, 3])
        self.assertEqual(self.t.successor(2), 3)

    def test_successor_in_next_cluster_current_cluster_only_has_min(self):
        self.t.update([1, 3])
        self.assertEqual(self.t.successor(1), 3)

    def test_successor_in_next_cluster_current_cluster_has_elements(self):
        self.t.update([0, 1, 3])
        self.assertEqual(self.t.successor(1), 3)

    def test_grow(self):
        t = vEBTree.of_size(2)
        self.assertEqual(t.universe_size, 2)

        t.add(2)
        self.assertEqual(t.universe_size, 4)
        self.assertIn(2, t)
        self.assertNotIn(3, t)

        t.add(7)
        self.assertEqual(t.universe_size, 8)
        self.assertIn(2, t)
        self.assertNotIn(3, t)
        self.assertIn(7, t)
        self.assertNotIn(6, t)

        t.add(195)
        self.assertEqual(t.universe_size, 256)

    def test_of_size(self):
        t = vEBTree.of_size(16)
        self.assertEqual(t.universe_size, 16)

    def test_update(self):
        self.t.update((1, 2))
        self.assertIn(1, self.t)
        self.assertIn(2, self.t)

    def test_init_adds_all_contents(self):
        t = vEBTree([1, 3, 15])
        self.assertEqual(t.universe_size, 16)
        self.assertIn(1, t)
        self.assertIn(3, t)
        self.assertIn(15, t)

    def test_equal_if_same_contents(self):
        t = vEBTree.of_size(self.t.universe_size)
        self.assertEqual(t, self.t)

        self.t.add(2)
        self.assertNotEqual(t, self.t)

        t.add(2)
        self.assertEqual(t, self.t)

        t.update([3, 5, 7])
        self.assertNotEqual(t, self.t)

        self.t.update([3, 5, 7])
        self.assertEqual(t, self.t)


class TestSize2VEBTree(TestCase, VEBTestMixin):
    def setUp(self):
        self.t = vEBTree.of_size(2)

    def test_add(self):
        self.t.add(0)
        self.assertIn(0, self.t)
        self.assertNotIn(1, self.t)

        self.t.add(1)
        self.assertIn(0, self.t)
        self.assertIn(1, self.t)

    def test_discard(self):
        self.assertNotIn(0, self.t)
        self.t.discard(0)
        self.assertNotIn(0, self.t)

        self.t.add(0)
        self.t.discard(0)
        self.assertNotIn(0, self.t)

    def test_min_max(self):
        self.assertIsNone(self.t.min)
        self.assertIsNone(self.t.max)

        self.t.add(0)
        self.assertEqual(self.t.min, 0)
        self.assertEqual(self.t.max, 0)

        self.t.add(1)
        self.assertEqual(self.t.min, 0)
        self.assertEqual(self.t.max, 1)

    def test_predecessor(self):
        self.assertIsNone(self.t.predecessor(0))
        self.assertIsNone(self.t.predecessor(1))

        self.t.add(0)
        self.assertIsNone(self.t.predecessor(0))
        self.assertEqual(0, self.t.predecessor(1))

    def test_successor(self):
        self.assertIsNone(self.t.successor(0))
        self.assertIsNone(self.t.successor(1))

        self.t.add(1)
        self.assertEqual(1, self.t.successor(0))
        self.assertIsNone(self.t.successor(1))


class TestEmptyVEBTree(TestCase, VEBTestMixin):
    def setUp(self):
        self.t = vEBTree()

    def test_size_0_makes_empty_tree(self):
        t = vEBTree.of_size(0)
        self.assertEqual(t.universe_size, 0)

    def test_universe_size(self):
        self.assertEqual(self.t.universe_size, 0)

    def test_repr(self):
        self.assertEqual(repr(self.t), "vEBTree([])")

    def test_bool(self):
        self.assertFalse(self.t)

    def test_contains(self):
        self.assertNotIn(0, self.t)

    def test_iter(self):
        self.assertEqual(list(self.t), [])

    def test_len(self):
        self.assertEqual(len(self.t), 0)

    def test_min(self):
        self.assertIsNone(self.t.min)

    def test_max(self):
        self.assertIsNone(self.t.max)

    def test_predecessor(self):
        self.assertIsNone(self.t.predecessor(0))

    def test_successor(self):
        self.assertIsNone(self.t.successor(0))

    def test_grow(self):
        self.t.grow(2)
        self.assertEqual(self.t.universe_size, 2)



class VEBQueueTest(object):
    @expectedFailure
    def testCreateNotEvenPowerOfTwo(self):
        self.assertRaises(IndexError, vEBTree.of_size, 0)
        self.assertRaises(IndexError, vEBTree.of_size, 3)

class LameQueue(object):
    def __init__(self):
        self.q = []

    def __contains__(self, x):
        locate = bisect.bisect_left(self.q, x)
        if locate == len(self.q) or self.q[locate] != x:
            return False
        return True

    def add(self, x):
        # Do a sorted insert
        insertion_point = bisect.bisect_left(self.q, x)
        if insertion_point == len(self.q) or self.q[insertion_point] != x:
            self.q.insert(insertion_point, x)

    def discard(self, x):
        insertion_point = bisect.bisect_left(self.q, x)
        if insertion_point < len(self.q) and self.q[insertion_point] == x:
            del self.q[insertion_point]

    def max(self):
        if len(self.q) > 0:
            return self.q[-1]
        return None

    def min(self):
        if len(self.q) > 0:
            return self.q[0]
        return None

    def predecessor(self, x):
        locate = bisect.bisect_left(self.q, x) - 1
        if locate >= 0:
            return self.q[locate]
        return None


class RandomTest(TestCase):
    def testRandom(self):
        n = 1 << 16
        totalOperations = 1 << 16
        operations = totalOperations

        q = vEBTree.of_size(n)
        lame = LameQueue()
        while operations > 0:
            # Do some searches
            numSearches = random.randint(0, 10)
            operations -= numSearches
            for i in range(numSearches):
                search = random.randint(0, n-1)
                r1 = search in lame
                r2 = search in q
                self.assertEqual(r1, r2)

                r1 = lame.predecessor(search)
                r2 = q.predecessor(search)
                self.assertEqual(r1, r2)

            # Change the queue state
            operations -= 1
            value = random.randint(0, n-1)
            stateChange = random.randint(0, 1)
            if stateChange == 0:
                q.add(value)
                lame.add(value)
                #~ print "add", value
            else:
                q.discard(value)
                lame.discard(value)
                #~ print "remove", value

            # Check the max/min variables
            assert lame.max() == q.max
            assert lame.min() == q.min
