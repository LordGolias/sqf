from unittest import TestCase

from core.exceptions import WrongTypes, IfThenSyntaxError
from core.types import String, Number, Array, Boolean, Nothing, Number as N
from core.interpreter import interpret


class TestInterpreter(TestCase):

    def test_one_statement(self):
        test = '_y = 2; _x = (_y == 3);'
        loc, outcome = interpret(test)
        self.assertEqual(Boolean(False), loc['_x'])
        self.assertEqual(Nothing, outcome)

    def test_var_not_defined(self):
        with self.assertRaises(WrongTypes):
            interpret('_y == 3;')

    def test_one_statement2(self):
        test = '(3 - 1) == (3 + 1)'
        loc, outcome = interpret(test)
        self.assertEqual(Boolean(False), outcome)

    def test_cant_compare_booleans(self):
        with self.assertRaises(WrongTypes):
            interpret('true == false;')

    def test_wrong_type_arithmetic(self):
        interpret('_x = true;')
        with self.assertRaises(WrongTypes):
            interpret('_x = true; _x + 2;')

    def test_code_dont_execute(self):
        loc, outcome = interpret('_x = true; {_x = false};')
        self.assertEqual(Boolean(True), loc['_x'])
        self.assertEqual(Nothing, outcome)

    def test_one_statement1(self):
        test = '_y = 2; (_y == 3)'
        loc, outcome = interpret(test)
        self.assertEqual(Boolean(False), outcome)

    def test_assign_to_statement(self):
        with self.assertRaises(WrongTypes):
            interpret('(_y) = 2;')

    def test_floor(self):
        _, outcome = interpret('floor 5.25')
        self.assertEqual(Number(5), outcome)

        _, outcome = interpret('floor -5.25')
        self.assertEqual(Number(-6), outcome)


class TestInterpretArray(TestCase):

    def test_assign(self):
        loc, outcome = interpret('_x = [1, 2];')
        self.assertEqual(Array([N(1), N(2)]), loc['_x'])

    def test_add(self):
        test = '_x = [1, 2]; _y = [3, 4]; _z = _x + _y'
        _, outcome = interpret(test)

        self.assertEqual(Array([N(1), N(2), N(3), N(4)]), outcome)

    def test_append(self):
        local, outcome = interpret('_x = [1, 2]; _x append [3, 4]')
        self.assertEqual(Nothing, outcome)
        self.assertEqual(Array([N(1), N(2), N(3), N(4)]), local['_x'])

    def test_subtract(self):
        test = '_x = [1, 2, 3, 2, 4]; _y = [2, 3]; _z = _x - _y'
        _, outcome = interpret(test)

        self.assertEqual(Array([N(1), N(4)]), outcome)

    def test_set(self):
        test = '_x = [1, 2]; _x set [0, 2];'
        local, _ = interpret(test)
        self.assertEqual(Array([N(2), N(2)]), local['_x'])

        test = '_x = [1, 2]; _x set [2, 3];'
        local, _ = interpret(test)
        self.assertEqual(Array([N(1), N(2), N(3)]), local['_x'])

    def test_in(self):
        _, outcome = interpret('2 in [1, 2]')
        self.assertEqual(Boolean(True), outcome)

        _, outcome = interpret('0 in [1, 2]')
        self.assertEqual(Boolean(False), outcome)

        _, outcome = interpret('[0, 1] in [1, [0, 1]]')
        self.assertEqual(Boolean(True), outcome)

    def test_select(self):
        _, outcome = interpret('[1, 2] select 0')
        self.assertEqual(N(1), outcome)

        # alternative using floats
        _, outcome = interpret('[1, 2] select 0.5')
        self.assertEqual(N(1), outcome)

        _, outcome = interpret('[1, 2] select 0.6')
        self.assertEqual(N(2), outcome)

        # alternative using booleans
        _, outcome = interpret('[1, 2] select true')
        self.assertEqual(N(2), outcome)

        _, outcome = interpret('[1, 2] select false')
        self.assertEqual(N(1), outcome)

        # alternative using [start, count]
        _, outcome = interpret('[1, 2, 3] select [1, 2]')
        self.assertEqual(Array([N(2), N(3)]), outcome)

        _, outcome = interpret('[1, 2, 3] select [1, 10]')
        self.assertEqual(Array([N(2), N(3)]), outcome)

    def test_find(self):
        _, outcome = interpret('[1, 2] find 2')
        self.assertEqual(N(1), outcome)

    def test_pushBack(self):
        loc, outcome = interpret('_x = [1]; _x pushBack 2')
        self.assertEqual(Array([N(1), N(2)]), loc['_x'])
        self.assertEqual(N(1), outcome)

    def test_pushBackUnique(self):
        loc, outcome = interpret('_x = [1]; _x pushBackUnique 2')
        self.assertEqual(Array([N(1), N(2)]), loc['_x'])
        self.assertEqual(N(1), outcome)

        loc, outcome = interpret('_x = [1, 2]; _x pushBackUnique 2')
        self.assertEqual(Array([N(1), N(2)]), loc['_x'])
        self.assertEqual(N(-1), outcome)

    def test_reverse(self):
        local, outcome = interpret('_x = [1, 2]; reverse _x')
        self.assertEqual(Nothing, outcome)
        self.assertEqual(Array([N(2), N(1)]), local['_x'])

    def test_reference(self):
        # tests that changing _x affects _y when _y = _x.
        loc, _ = interpret('_x = [1, 2]; _y = _x; _x set [0, 2];')
        self.assertEqual(Array([N(2), N(2)]), loc['_x'])
        self.assertEqual(Array([N(2), N(2)]), loc['_y'])

        loc, _ = interpret('_x = [1, 2]; _y = _x; reverse _x;')
        self.assertEqual(Array([N(2), N(1)]), loc['_y'])


class TestInterpretString(TestCase):
    def test_assign(self):
        test = '_x = "ABA";'
        loc, outcome = interpret(test)

        self.assertEqual(String('ABA'), loc['_x'])

    def test_add(self):
        test = '_x = "ABA"; _y = "BAB"; _x + _y'
        _, outcome = interpret(test)
        self.assertEqual(String('ABABAB'), outcome)

    def test_find(self):
        _, outcome = interpret('"Hello world!" find "world!"')
        self.assertEqual(N(6), outcome)


class IfThen(TestCase):
    def test_then(self):
        loc, outcome = interpret('_x = 1; if (true) then {_x = 2}')
        self.assertEqual(N(2), outcome)
        self.assertEqual(N(2), loc['_x'])

        loc, outcome = interpret('_x = 1; if (false) then {_x = 2}')
        self.assertEqual(Nothing, outcome)
        self.assertEqual(N(1), loc['_x'])

    def test_then_array(self):
        loc, outcome = interpret('if (true) then [{_x = 2}, {_x = 3}]')
        self.assertEqual(N(2), outcome)
        self.assertEqual(N(2), loc['_x'])

        loc, outcome = interpret('if (false) then [{_x = 2}, {_x = 3}]')
        self.assertEqual(N(3), outcome)
        self.assertEqual(N(3), loc['_x'])

    def test_then_else(self):
        loc, outcome = interpret('if (true) then {_x = 2} else {_x = 3}')
        self.assertEqual(N(2), outcome)
        self.assertEqual(N(2), loc['_x'])

        loc, outcome = interpret('if (false) then {_x = 2} else {_x = 3}')
        self.assertEqual(N(3), outcome)
        self.assertEqual(N(3), loc['_x'])

    def test_exceptions(self):
        with self.assertRaises(IfThenSyntaxError):
            interpret('if (false) then (_x = 2) else {_x = 3}')

        with self.assertRaises(WrongTypes):
            interpret('if (1) then {_x = 2} else {_x = 3}')


class Scopes(TestCase):

    def test_assign(self):
        local_scope, outcome = interpret('x = 2; _x = 1;')

        self.assertEqual(N(1), local_scope.values['_x'])
        self.assertEqual(N(2), local_scope.values['x'])

    def test_one_scope(self):
        local_scope, outcome = interpret('_x = 1;')
        self.assertEqual(N(1), local_scope.values['_x'])

        local_scope, outcome = interpret('_x = 1; if true then {_x}')
        self.assertEqual(N(1), outcome)

        local_scope, outcome = interpret('_x = 1; if (true) then {private "_x"; _x}')
        self.assertEqual(Nothing, outcome)

        local_scope, outcome = interpret('_x = 1; if (true) then {private "_x"; _x = 2}')
        self.assertEqual(N(2), outcome)
        self.assertEqual(N(1), local_scope['_x'])

        # without private, set it to the outermost scope
        local_scope, outcome = interpret('_x = 1; if (true) then {_x = 2}')
        self.assertEqual(N(2), outcome)
        self.assertEqual(N(2), local_scope['_x'])

    def test_private_global_error(self):
        with self.assertRaises(SyntaxError):
            interpret('private "x"')

    def test_function(self):
        scope, outcome = interpret('_max = {(_this select 0) max (_this select 1)};'
                                   '_maxValue = [3,5] call _max;')
        self.assertEqual(N(5), scope['_maxValue'])
