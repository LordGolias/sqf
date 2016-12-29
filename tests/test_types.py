from unittest import TestCase

from core.types import String, ForEach, Array, Nil, Comma, Boolean, Nothing, \
    Variable as V, OPERATORS as OP, Number as N


class TestTypesToString(TestCase):

    def test_bool(self):
        self.assertEqual('true', str(Boolean(True)))
        self.assertEqual('false', str(Boolean(False)))

    def test_number(self):
        self.assertEqual('1', str(N(1)))
        self.assertEqual('1.10', str(N(1.1)))

    def test_array(self):
        self.assertEqual('[1, 1]', str(Array([1, 1])))

    def test_reservedtoken(self):
        self.assertEqual('foreach', str(ForEach))

    def test_nothing(self):
        self.assertEqual('Nothing', str(Nothing))
