from unittest import TestCase

from sqf.parser import parse
from sqf.analyser import analyze


class AnalyserTestCase(TestCase):

    def test_statement(self):
        code = '_x=2 _y=3;'
        result = parse(code)

        errors = analyze(result)

        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 6), errors[0].position)

    def test_code(self):
        code = "x = {\n    call {_x=1 _y = 2;}\n}"
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((2, 16), errors[0].position)

    def test_code1(self):
        code = "_damage = 0\nif (not _onoff) then {_damage = 0.95;};"
        result = parse(code)
        errors = analyze(result)
        self.assertEqual(len(errors), 1)
        self.assertEqual((2, 1), errors[0].position)

    def test_private1(self):
        code = "private _posicion = _location call AS_fnc_location_position;"
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_foreach(self):
        code = "{sleep 1} forEach _lamps;"
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_getConfig(self):
        code = 'configFile >> "CfgWeapons" >> _name >> "WeaponSlotsInfo" >> "mass"'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_lowercase(self):
        code = 'mapa = "MapBoard_altis_F" createvehicle [0,0,0];'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_define_simple(self):
        code = "#define CHECK_CATEGORY 2\n"
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_define_error(self):
        code = "#define\n"
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 1), errors[0].position)

    def test_define(self):
        code = '#define CHECK_CATEGORY(_category) (if !(_category in AS_AAFarsenal_categories) then { \\\n' \
               '\tdiag_log format ["[AS] AS_AAFarsenal: category %1 does not exist.", _category];} \\\n    );\n'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_include(self):
        code = '#include "macros.hpp"\n_x = 1;'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_include_error(self):
        code = '#include _x\n'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 1), errors[0].position)

    def test_include_error_len(self):
        code = '#include\n'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 1), errors[0].position)

    def test_for_missing_do(self):
        code = 'for "_i" from 1 to 10 {y pushBack _i;};'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 23), errors[0].position)

    def test_if_missing_then(self):
        code = 'if (true) {1}'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 11), errors[0].position)

    def test_while(self):
        code = 'while {count _roads > 0} do {}'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_foreach_statement(self):
        code = '{} foreach ();'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)


class SwitchTestCase(TestCase):

    def test_no_double_colon(self):
        code = 'switch (0) do {case 1, {"one"};}'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 22), errors[0].position)

    def test_not_statement(self):
        code = 'switch (1) do {case 1: {"one"};}'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_not_switch_statement(self):
        code = 'switch _x do {case 1: {"one"};}'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 7), errors[0].position)

    def test_missing_do(self):
        code = 'switch (_x) {case 1: {"one"};}'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 13), errors[0].position)

    def test_incomplete_case(self):
        code = 'switch (_x) do {case 1: }'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 17), errors[0].position)

    def test_case_without_code(self):
        code = 'switch (_x) do {case 1: 2}'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 25), errors[0].position)

    def test_default(self):
        code = 'default {[]};'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 0)

    def test_default_error(self):
        code = 'default : {[]};'
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 9), errors[0].position)
