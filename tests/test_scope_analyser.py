from unittest import TestCase

from sqf.types import Number
from sqf.parser import parse
from sqf.scope_analyser import interpret


class ScopeAnalyserTestCase(TestCase):

    def test_warn_not_in_scope(self):
        analyser = interpret(parse('private _y = _z;'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 14), errors[0].position)

    def test_assign_wrong(self):
        analyser = interpret(parse('1 = 2;'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 1), errors[0].position)

    def test_private_eq(self):
        analyser = interpret(parse('private _x = 2; _z = _x + 1;'))
        errors = analyser.exceptions

        self.assertEqual(len(errors), 1)
        self.assertEqual(Number(2), analyser['_x'])

    def test_private_eq1(self):
        analyser = interpret(parse('private _x = 1 < 2;'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_private_single(self):
        code = 'private "_x"; private _z = _x;'
        analyser = interpret(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_private_many(self):
        analyser = interpret(parse('private ["_x", "_y"];'))
        errors = analyser.exceptions
        self.assertTrue('_x' in analyser)
        self.assertTrue('_y' in analyser)
        self.assertEqual(len(errors), 0)

    def test_private_wrong(self):
        # private argument must be a string
        analyser = interpret(parse('private _x;'))
        errors = analyser.exceptions

        self.assertEqual(len(errors), 1)

    def test_private_wrong_exp(self):
        # private argument must be a string
        analyser = interpret(parse('private {_x};'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test__this(self):
        analyser = interpret(parse('private _nr = _this select 0;'))
        errors = analyser.exceptions

        self.assertEqual(len(errors), 0)

    def test_global(self):
        # global variables have no error
        analyser = interpret(parse('private _nr = global select 0;'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_set_and_get_together(self):
        # because _x is assigned to the outer scope, reading it is also from
        # the outer scope.
        analyser = interpret(parse('_x =+ global; private _y = _x'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_params_single(self):
        analyser = interpret(parse('params ["_x"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertTrue('_x' in analyser)
        self.assertTrue('"_x"' not in analyser)

    def test_params_double(self):
        analyser = interpret(parse('params ["_x", "_y"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_params_array(self):
        analyser = interpret(parse('params [["_x", 0], "_y"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(Number(0), analyser['_x'])

    def test_params_array_wrong(self):
        analyser = interpret(parse('params [["_x"], "_y"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_params_wrong_array_element(self):
        analyser = interpret(parse('params [1]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_params_wrong_argument(self):
        analyser = interpret(parse('params {1}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_params_with_prefix(self):
        analyser = interpret(parse('[] params ["_x"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_params_with_empty_string(self):
        analyser = interpret(parse('params [""]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_error_inside_array(self):
        code = '_x = []; [1, _x select 0];'
        analyser = interpret(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_code(self):
        code = 'if (false) then {_damage = 0.95;};'
        analyser = interpret(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)


class ScopeAnalyserDefineTestCase(TestCase):

    def test_define_simple(self):
        code = "#define A (true)\nprivate _x = A;"
        analyser = interpret(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_define(self):
        code = "#define A(_x) (_x == 2)\nprivate _x = A(3);"
        analyser = interpret(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
