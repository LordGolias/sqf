from unittest import TestCase

from core.exceptions import SyntaxError, UnbalancedParenthesisSyntaxError, IfThenSyntaxError, WrongTypes
from core.types import String, ForEach, Array, Nil, Comma, Boolean, Nothing, \
    Variable as V, Number as N
from core.operators import OPERATORS as OP
from core.statements import Statement, IfThenStatement
from core.interpreter import interpret


class TestInterpreter(TestCase):

    def test_one_statement(self):
        test = '_y = 2; _x = (_y == 3);'
        glob, loc, outcome = interpret(test)
        self.assertEqual(Boolean(False), loc.variables_values['_x'])
        self.assertEqual(Nothing, outcome)

    def test_var_not_defined(self):
        with self.assertRaises(WrongTypes):
            interpret('_y == 3;')

    def test_one_statement2(self):
        test = '(3 - 1) == (3 + 1)'
        glob, loc, outcome = interpret(test)
        self.assertEqual(Boolean(False), outcome)

    def test_cant_compare_booleans(self):
        with self.assertRaises(WrongTypes):
            interpret('true == false;')

    def test_wrong_type_arithmetic(self):
        interpret('_x = true;')
        with self.assertRaises(WrongTypes):
            interpret('_x = true; _x + 2;')

    def test_brackets(self):
        glob, loc, outcome = interpret('_x = true; {_x = false}')
        self.assertEqual(Boolean(True), loc.variables_values['_x'])
        self.assertEqual(Boolean(False), outcome)

    def test_one_statement1(self):
        test = '_y = 2; (_y == 3)'
        glob, loc, outcome = interpret(test)
        self.assertEqual(Boolean(False), outcome)


class TestInterpretArray(TestCase):

    def test_assign(self):
        glob, loc, outcome = interpret('_x = [1, 2];')
        self.assertEqual(Array([N(1), N(2)]), loc.variables_values['_x'])

    def test_add(self):
        test = '_x = [1, 2]; _y = [3, 4]; _z = _x + _y'
        _, _, outcome = interpret(test)

        self.assertEqual(Array([N(1), N(2), N(3), N(4)]), outcome)

    def test_append(self):
        _, local, outcome = interpret('_x = [1, 2]; _x append [3, 4]')
        self.assertEqual(Nothing, outcome)
        self.assertEqual(Array([N(1), N(2), N(3), N(4)]), local.variables_values['_x'])

    def test_subtract(self):
        test = '_x = [1, 2, 3, 2, 4]; _y = [2, 3]; _z = _x - _y'
        _, _, outcome = interpret(test)

        self.assertEqual(Array([N(1), N(4)]), outcome)

    def test_set(self):
        test = '_x = [1, 2]; _x set [0, 2];'
        _, local, _ = interpret(test)
        self.assertEqual(Array([N(2), N(2)]), local.variables_values['_x'])

        test = '_x = [1, 2]; _x set [2, 3];'
        _, local, _ = interpret(test)
        self.assertEqual(Array([N(1), N(2), N(3)]), local.variables_values['_x'])

    def test_in(self):
        _, _, outcome = interpret('2 in [1, 2]')
        self.assertEqual(Boolean(True), outcome)

        _, _, outcome = interpret('0 in [1, 2]')
        self.assertEqual(Boolean(False), outcome)

        _, _, outcome = interpret('[0, 1] in [1, [0, 1]]')
        self.assertEqual(Boolean(True), outcome)

    def test_select(self):
        _, _, outcome = interpret('[1, 2] select 0')
        self.assertEqual(N(1), outcome)

        # alternative using floats
        _, _, outcome = interpret('[1, 2] select 0.5')
        self.assertEqual(N(1), outcome)

        _, _, outcome = interpret('[1, 2] select 0.6')
        self.assertEqual(N(2), outcome)

        # alternative using booleans
        _, _, outcome = interpret('[1, 2] select true')
        self.assertEqual(N(2), outcome)

        _, _, outcome = interpret('[1, 2] select false')
        self.assertEqual(N(1), outcome)

        # alternative using [start, count]
        _, _, outcome = interpret('[1, 2, 3] select [1, 2]')
        self.assertEqual(Array([N(2), N(3)]), outcome)

        _, _, outcome = interpret('[1, 2, 3] select [1, 10]')
        self.assertEqual(Array([N(2), N(3)]), outcome)

    def test_find(self):
        _, _, outcome = interpret('[1, 2] find 2')
        self.assertEqual(N(1), outcome)

    def test_pushBack(self):
        _, loc, outcome = interpret('_x = [1]; _x pushBack 2')
        self.assertEqual(Array([N(1), N(2)]), loc.variables_values['_x'])
        self.assertEqual(N(1), outcome)

    def test_pushBackUnique(self):
        _, loc, outcome = interpret('_x = [1]; _x pushBackUnique 2')
        self.assertEqual(Array([N(1), N(2)]), loc.variables_values['_x'])
        self.assertEqual(N(1), outcome)

        _, loc, outcome = interpret('_x = [1, 2]; _x pushBackUnique 2')
        self.assertEqual(Array([N(1), N(2)]), loc.variables_values['_x'])
        self.assertEqual(N(-1), outcome)

    def test_reverse(self):
        _, local, outcome = interpret('_x = [1, 2]; reverse _x')
        self.assertEqual(Nothing, outcome)
        self.assertEqual(Array([N(2), N(1)]), local.variables_values['_x'])

    def test_reference(self):
        # tests that changing _x affects _y when _y = _x.
        _, loc, _ = interpret('_x = [1, 2]; _y = _x; _x set [0, 2];')
        self.assertEqual(Array([N(2), N(2)]), loc.variables_values['_x'])
        self.assertEqual(Array([N(2), N(2)]), loc.variables_values['_y'])

        _, loc, _ = interpret('_x = [1, 2]; _y = _x; reverse _x;')
        self.assertEqual(Array([N(2), N(1)]), loc.variables_values['_y'])


class TestInterpretString(TestCase):
    def test_assign(self):
        test = '_x = "ABA";'
        glob, loc, outcome = interpret(test)

        self.assertEqual(String('ABA'), loc.variables_values['_x'])

    def test_add(self):
        test = '_x = "ABA"; _y = "BAB"; _x + _y'
        _, _, outcome = interpret(test)
        self.assertEqual(String('ABABAB'), outcome)

    def test_find(self):
        _, _, outcome = interpret('"Hello world!" find "world!"')
        self.assertEqual(N(6), outcome)
