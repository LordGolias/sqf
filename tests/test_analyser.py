from unittest import TestCase, expectedFailure

from sqf.types import Number, String, Boolean, Nothing, Array
from sqf.parser import parse
from sqf.analyser import analyze, Analyzer


class GeneralTestCase(TestCase):

    def test_insensitive_variables(self):
        code = 'private "_x"; a = _X'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_warn_not_in_scope(self):
        analyser = analyze(parse('private _y = _z;'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 14), errors[0].position)

    def test_evaluate(self):
        code = 'private _x = 2;'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(Number(), analyser['_x'])

    def test_assign_wrong(self):
        analyser = analyze(parse('1 = 2;'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 1), errors[0].position)

    def test_private_eq1(self):
        analyser = analyze(parse('private _x = 1 < 2;'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_private_single(self):
        code = 'private "_x"; private _z = _x;'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_private_many(self):
        analyser = analyze(parse('private ["_x", "_y"];'))
        errors = analyser.exceptions
        self.assertTrue('_x' in analyser)
        self.assertTrue('_y' in analyser)
        self.assertEqual(len(errors), 0)

    def test_private_wrong(self):
        # private argument must be a string
        analyser = analyze(parse('private _x;'))
        errors = analyser.exceptions

        self.assertEqual(len(errors), 1)

    def test_private_wrong_exp(self):
        # private argument must be a string
        analyser = analyze(parse('private {_x};'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_private_no_errors(self):
        code = "private _posicion = x call AS_fnc_location_position;"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test__this(self):
        analyser = analyze(parse('private _nr = _this select 0;'))
        errors = analyser.exceptions

        self.assertEqual(len(errors), 0)

    def test_global(self):
        # global variables have no error
        analyser = analyze(parse('private _nr = global select 0;'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_set_and_get_together(self):
        # because _x is assigned to the outer scope, reading it is also from
        # the outer scope.
        analyser = analyze(parse('_x =+ global; private _y = _x'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_wrong_semi_colon(self):
        code = 'if; (false) then {x = 0.95;};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)
        self.assertEqual((1, 1), errors[0].position)

    def test_undefined_sum(self):
        code = 'y = x + 1'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_wrong_sum(self):
        code = 'y = x + z'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'y = x + do'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_missing_semi_colon(self):
        code = "d = 0\nif (not onoff) then {d = 0.95;};"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)
        self.assertEqual((1, 4), errors[0].position)

    def test_statement(self):
        code = 'x=2 y=3;'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 3), errors[0].position)

    @expectedFailure
    def test_missing_op(self):
        """
        Still no way to distinguish this from the one below
        """
        code = 'x 2'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_if_then(self):
        code = 'if (false) then {_damage = 0.95;};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_if_then_else(self):
        code = 'if (false) then\n {_damage = 0.95}\n\telse\n\t{_damage = 1};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_if_then_specs(self):
        code = 'if (false) then [{_damage = 0.95},{_damage = 1}]'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_if(self):
        code = 'if (not _onoff) then {_damage = 0.95;};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_while(self):
        code = 'while {true} do {_x = 2}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_for_specs(self):
        code = 'for [{_x = 1},{_x <= 10},{_x = _x + 1}] do {_y = _y + 2}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 6)

    def test_for_code(self):
        code = 'private _x = {hint str _y}; for "_i" from 0 to 10 do _x'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_foreach_error(self):
        code = '{hint str _y} forEach [1,2]'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_foreach_variable(self):
        code = '{hint str _y} forEach _d;'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_foreach_no_error(self):
        code = "{sleep 1} forEach lamps;"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_getConfig(self):
        code = 'configFile >> "CfgWeapons" >> x >> "WeaponSlotsInfo" >> "mass"'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_custom_function(self):
        code = 'a = createMarker ["a", [0,0,0]];'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_get_variable_unknown_first_element(self):
        code = 'missionNamespace getVariable[format["x_%1",x],[]];'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_lowercase(self):
        code = 'mapa = "MapBoard_altis_F" createvehicle [0,0,0];'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_for_missing_do(self):
        code = 'for "_i" from 1 to 10 {y pushBack _i;};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 3)
        self.assertEqual((1, 20), errors[0].position)

    def test_if_missing_then(self):
        code = 'if (true) {1}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)
        self.assertEqual((1, 4), errors[0].position)

    def test_while_no_errors(self):
        code = 'while {count x > 0} do {}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_foreach_no_errors(self):
        code = '{} foreach ();'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_wrong_if(self):
        code = 'if ;'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_negation_priority(self):
        code = '!isNull x'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_priority(self):
        code = '(x) isEqualTo -1'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_precedence_nullary(self):
        code = 'x = !isServer;'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_error_message_unary(self):
        code = 'parseNumber 1'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].message,
                         'error:Unary operator "parseNumber" only accepts argument '
                         'of types [String,Boolean] (rhs is Number)')

    def test_error_message_binary(self):
        code = '1 + "2"'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].message.startswith('error:Binary operator "+" arguments must be ['))

    def test_error_in(self):
        code = '_door ()'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_handgunMagazine_is_array(self):
        code = 'private _x = ""; private _m = handgunMagazine player; _x = _m select 0;'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_count_with_config_and_minus(self):
        code = 'x = missionConfigFile >> "CfgInteractionMenus"; for "_n" from 0 to count(x) - 1 do {}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_error_bla(self):
        code = '() ()'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_error_double(self):
        code = 'private["_x","_y"];\n_x _y'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_missing_while_bracket(self):
        code = 'while ((count x) < y) do {}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_throw(self):
        analyser = analyze(parse('if () throw false'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_precedence_various(self):
        code = 'surfaceIsWater getPos player'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'str floor x'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'floor random 3'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'floor -2'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'x lbSetCurSel -1'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_getset_variable_undefined(self):
        code = 'missionNamespace getVariable x'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'missionNamespace getVariable [x,2]'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'x = str y; missionNamespace getVariable x'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'missionNamespace setVariable [x,2]'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'missionNamespace setVariable x'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    @expectedFailure
    def test_precedence_fail(self):
        code = 'x % floor x'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_logical_with_nothing(self):
        code = '{true || x} forEach [1,2]'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_call_recursive(self):
        code = '''x = {call x}; call x'''
        analyze(parse(code))

    def test_with_namespace_simple(self):
        code = 'with uinamespace do {_x; x = 2}'
        analyser = analyze(parse(code))
        self.assertEqual(len(analyser.exceptions), 1)
        self.assertEqual(Nothing, type(analyser['x'])) # missionnamespace is empty
        self.assertEqual(Number, type(analyser.namespace('uinamespace')['x']))

    def test_with_namespace(self):
        code = 'with uinamespace do {with missionnamespace do {x = 2}}'
        analyser = analyze(parse(code))
        self.assertEqual(Number, type(analyser['x'])) # missionnamespace is empty
        self.assertEqual(Nothing, type(analyser.namespace('uinamespace')['x']))


class Preprocessor(TestCase):

    def test_define_simple(self):
        code = "#define A (true)\nprivate _x = A;"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_define(self):
        code = "#define A(_x) (_x == 2)\nprivate _x = A(3);"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_define_no_error(self):
        code = "#define CHECK_CATEGORY 2\n"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_define_error(self):
        code = "#define\n"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 1), errors[0].position)

    def test_define_complex(self):
        code = '#define CHECK_CATEGORY(_category) (if !(_category in AS_AAFarsenal_categories) then { \\\n' \
               '\tdiag_log format ["[AS] AS_AAFarsenal: category %1 does not exist.", _category];} \\\n    );\n'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_include(self):
        code = '#include "macros.hpp"\nx = 1;'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_include_error(self):
        code = '#include _x\n'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 1), errors[0].position)

    def test_include_error_len(self):
        code = '#include\n'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 1), errors[0].position)

    def test_macros(self):
        code = 'x call EFUNC(api,setMultiPushToTalkAssignment)'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_ifdef_endif(self):
        code = '#ifdef A\nA = 1;#endif'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_define_usage(self):
        code = "#define __CHECK_CATEGORY 2\nx = __CHECK_CATEGORY"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(analyser['x'], Number())

    def test_define_with_args_usage(self):
        code = "#define __CHECK_CATEGORY(_x) (_x)\n"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_define_with_define(self):
        code = "#define PASS(x) PUSH(x,y)\n"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_defines(self):
        # ignore "macros" (not correct since CHECK may not be defined, but for that we need a pre-processor)
        code = 'CHECK(x)'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_define_correct(self):
        # ignore "macros" (not correct since CHECK may not be defined, bot for that we need a pre-processor)
        code = '#define A'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_call_within(self):
        analyser = analyze(parse('LOG("")'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)


class Arrays(TestCase):

    def test_basic(self):
        code = 'a=[_x,\n_y]'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)
        self.assertEqual((1, 4), errors[0].position)
        self.assertEqual((2, 1), errors[1].position)

    def test_error_inside_array(self):
        code = 'x=[1, _x select 0];'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].position, (1, 7))

    def test_no_space(self):
        code = 'x set[_cIndex, 2]'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 7), errors[0].position)

    def test_strange(self):
        code = '{\n\tformat ["",\n\t\t\t_z, _y];\n} forEach a;\n'
        analyser = analyze(parse(code))
        errors = analyser.exceptions

        self.assertEqual(len(errors), 2)
        self.assertEqual((3, 8), errors[1].position)

    def test_position_of_array(self):
        code = 'y = if (x) then[{hint _x}, {damage _y}];'
        analyser = analyze(parse(code))
        self.assertEqual(len(analyser.exceptions), 2)
        self.assertEqual((1, 36), analyser.exceptions[1].position)
        self.assertEqual((1, 23), analyser.exceptions[0].position)

    def test_array_from_function(self):
        code = '("" configClasses configFile)'
        analyser = analyze(parse(code))
        self.assertEqual(len(analyser.exceptions), 0)

        code = '("" configClasses configFile) select 2'
        analyser = analyze(parse(code))
        self.assertEqual(len(analyser.exceptions), 0)


class Switch(TestCase):

    def test_case_not_code(self):
        code = 'switch (x) do {case 1: 2}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 22), errors[0].position)

    def test_incomplete_case(self):
        code = 'switch (x) do {case 1: }'
        analyser = analyze(parse(code))
        self.assertEqual(len(analyser.exceptions), 1)
        self.assertEqual((1, 16), analyser.exceptions[0].position)

    def test_case_by_variable(self):
        code = 'switch (a) do {case "blue": x; case "red": {false}}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_error_in_case(self):
        code = 'switch (a) do {case "blue": {hint _x}; case "red": {false}}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_case_with_variable_code(self):
        code = 'switch (x) do {case 1: _y}'
        analyser = analyze(parse(code))
        self.assertEqual(len(analyser.exceptions), 1)

    def test_default(self):
        code = 'switch (x) do {default {[]}}'
        analyser = analyze(parse(code))
        self.assertEqual(len(analyser.exceptions), 0)

    def test_default_error(self):
        code = 'switch (x) do {default : {[]}}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)
        self.assertEqual((1, 16), errors[0].position)

    def test_switch_statement_without_parenthesis(self):
        code = 'switch 1 do {case 1: {"one"};}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_not_statement(self):
        code = 'switch (1) do {case 1: {"one"};}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_missing_do(self):
        code = 'switch (1) {case 1: {"one"};}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 8), errors[0].position)

    def test_switch_alone(self):
        code = 'switch (x) do {case "ACRE_PRC343";};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)


class NestedCode(TestCase):
    def test_code(self):
        code = "x = {\ncall {x=1 y = 2;}\n}"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((2, 9), errors[0].position)

    def test_array_after_then(self):
        code = 'if (x) then[{},{}];'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_array(self):
        code = '[{\n3 2},0,0];'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((2, 1), errors[0].position)

    def test_code_with_private(self):
        code = "x = {\ncall {private _x;}\n}"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((2, 15), errors[0].position)

    def test_code_with_expression(self):
        code = "x = {\ncall {1 + _x;}\n}"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((2, 11), errors[0].position)

    def test_code_with_if(self):
        code = "x = {\ncall {if y;}\n}"
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
        self.assertEqual((2, 7), errors[0].position)

    def test_private(self):
        code = 'private _x = 2; while {_x < 1} do {}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_private_in_exitwith(self):
        code = 'private _x = 2; if (true) exitWith {x = _x}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_call_within(self):
        analyser = analyze(parse('x = 0; call {call {x = x + 1; call {x = x + 2}}}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_change_types(self):
        """
        When branched code changes variable type, we make it Nothing
        since we do not know which branch it took.
        """
        code = 'x = 1; if (y) then {x = ""};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(Nothing, type(analyser['x']))

    @expectedFailure
    def test_change_types1(self):
        code = 'x = 1; if (y) then {x = ""} else {x = "string"};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(Nothing, type(analyser['x']))


class Params(TestCase):

    def test_params_single(self):
        analyser = analyze(parse('params ["_x"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertTrue('_x' in analyser)
        self.assertTrue('"_x"' not in analyser)

    def test_params_double(self):
        analyser = analyze(parse('params ["_x", "_y"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_params_array(self):
        analyser = analyze(parse('params [["_x", 0], "_y"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(Nothing(), analyser['_x'])

    def test_params_with_prefix(self):
        analyser = analyze(parse('[] params ["_x"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_params_with_empty_string(self):
        analyser = analyze(parse('params [""]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_params(self):
        code = 'params [["_player",objNull,[objNull]],["_isMale",true]];'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_params_array_wrong(self):
        analyser = analyze(parse('params [["_x"], "_y"]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_params_wrong_array_element(self):
        analyser = analyze(parse('params [1]'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_params_wrong_argument(self):
        analyser = analyze(parse('params {1}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)


class SpecialContext(TestCase):
    def test_insensitive__foreachindex(self):
        code = '{_foreachindex} forEach [0]'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_try_catch(self):
        code = 'try {hint _x} catch {hint _y; hint str _exception}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_for_scope(self):
        code = 'for "_i" from 0 to 10 do {_i}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_for_scope_new(self):
        code = 'for "_i" from 0 to 10 do {_lamp = _i}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_foreach(self):
        code = '{hint str _x} forEach [1,2]'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_select_count_apply(self):
        code = '{_x == 2} count x'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'x select {_x == 2}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'x apply {_x == 2}'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = 'x select {_x == _y}' # _y is undefined
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_code_not_executed_in_loop(self):
        code = '{if ((_x select 0) == r && {(_x select 1) == r}) exitWith {};} forEach t;'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

        code = '(allVariables _this) select {!(isNil {_this getVariable _x})};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_issue5(self):
        code = 'private _view = cameraView;if (!isNull objectParent player && {_view == "GUNNER"}) then {};'
        analyser = analyze(parse(code))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)


class UndefinedValues(TestCase):
    """
    Test what happens when a value is not defined.
    """
    def test_number(self):
        code = "y = 2 + x"
        analyzer = Analyzer()
        scope = analyzer.get_scope('x')
        scope['x'] = Number()

        analyze(parse(code), analyzer)
        errors = analyzer.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(analyzer['y'], Number())

    def test_string(self):
        code = "y = 'x' + x"
        analyzer = Analyzer()
        scope = analyzer.get_scope('x')
        scope['x'] = String()

        analyze(parse(code), analyzer)
        errors = analyzer.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(analyzer['y'], String())

    def test_boolean(self):
        code = "y = true || x"
        analyzer = Analyzer()
        scope = analyzer.get_scope('x')
        scope['x'] = Boolean()

        analyze(parse(code), analyzer)
        errors = analyzer.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(analyzer['y'], Boolean())

    def test_array(self):
        code = "y = x select 2"

        analyzer = Analyzer()
        scope = analyzer.get_scope('x')
        scope['x'] = Array()

        analyze(parse(code), analyzer)
        self.assertEqual(len(analyzer.exceptions), 0)
        self.assertEqual(analyzer['y'], Nothing())

    def test_array2(self):
        analyser = analyze(parse('allPlayers select [1,2];'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)

    def test_if(self):
        # undefined -> do neither and invalidate any assigment
        analyser = analyze(parse('x=2; if (y) then {x=1} else {x=2}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(Number(), analyser['x'])

        # undefined -> test then
        analyser = analyze(parse('if (y) then {!1}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

        # undefined -> test both
        analyser = analyze(parse('if (y) then {!1} else {!2}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 2)

    def test_while(self):
        # undefined -> do not iterate
        analyser = analyze(parse('while {x != 0} do {x = 1}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(Number(), analyser['x'])

        # undefined -> test
        analyser = analyze(parse('while {x != 0} do {! 1}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_for(self):
        # undefined -> do not execute
        analyser = analyze(parse('x = 0; for "_i" from 0 to y do {x = x + 1}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(Number(), analyser['x'])

        # undefined -> test
        analyser = analyze(parse('x = 0; for "_i" from 0 to y do {!1}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)

    def test_forspecs(self):
        # undefined -> do not execute
        analyser = analyze(parse('y = 0; for [{x = 1},{x <= z},{x = x + 1}] do {y = y + 1}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 0)
        self.assertEqual(Number(), analyser['y'])

        # undefined -> test
        analyser = analyze(parse('y = 0; for [{x = 1},{x <= z},{x = x + 1}] do {!1}'))
        errors = analyser.exceptions
        self.assertEqual(len(errors), 1)
