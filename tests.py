import unittest

from parse_exp import parse_exp, partition
from exceptions import SyntaxError, NotATypeError, SyntaxIfThenError
from core.types import String, IfToken, ThenToken
from parser import parse, Statement, AssignmentStatement, LogicalStatement, parse_strings, tokenize
from parser import Variable as V, OPERATORS as OP


class TestExpParser(unittest.TestCase):

    def test_partition(self):
        res = partition([V('_x'), OP['='], V('2')], OP['='], list)
        self.assertEqual([[V('_x')], OP['='], [V('2')]], res)

    def test_binary(self):
        # a=b
        test = [V('a'), OP['='], V('b')]
        self.assertEqual([V('a'), OP['='], V('b')], parse_exp(test, [OP['=']]))

        # a=b+c*d
        test = [V('a'), OP['='], V('b'), OP['+'], V('c'), OP['*'], V('d')]
        self.assertEqual([V('a'), OP['='], [V('b'), OP['+'], [V('c'), OP['*'], V('d')]]],
                         parse_exp(test, [OP['='], OP['+'], OP['*']]))

    def test_binary_two_same_operators(self):
        # a=b=e+c*d
        test = [V('a'), OP['='], V('b'), OP['='], V('e'), OP['+'], V('c'), OP['*'], V('d')]
        self.assertEqual([V('a'), OP['='], [V('b'), OP['='], [V('e'), OP['+'], [V('c'), OP['*'], V('d')]]]],
                         parse_exp(test, [OP['='], OP['+'], OP['*']]))

        # a+b+c
        test = [V('a'), OP['+'], V('b'), OP['+'], V('c')]
        self.assertEqual([V('a'), OP['+'], [V('b'), OP['+'], V('c')]],
                         parse_exp(test, [OP['='], OP['+'], OP['*']]))

    def test_binary_order_matters(self):
        # a+b=c
        test = [V('a'), OP['+'], V('b'), OP['='], V('c')]
        self.assertEqual([[V('a'), OP['+'], V('b')], OP['='], V('c')],
                         parse_exp(test, [OP['='], OP['+'], OP['*']]))

    def test_unary(self):
        # a=!b||c
        test = [V('a'), OP['='], OP['!'], V('b'), OP['||'], V('c')]
        self.assertEqual([V('a'), OP['='], [[OP['!'], V('b')], OP['||'], V('c')]],
                         parse_exp(test, [OP['='], OP['||'], OP['!']]))

    def test_with_statement(self):
        test = Statement([V('a'), OP['+'], V('b'), OP['='], V('c')])
        self.assertEqual(Statement([Statement([V('a'), OP['+'], V('b')]), OP['='], V('c')]),
                         parse_exp(test, [OP['='], OP['+'], OP['*']]))


class TestParse(unittest.TestCase):

    def test_two_statements(self):
        result = parse('_x setvariable 2; _y setvariable 3;')

        self.assertEqual('_x setvariable 2; _y setvariable 3;',
                         str(result))

        self.assertEqual(len(result), 2)
        self.assertTrue(isinstance(result[0], Statement))
        self.assertEqual(str(result[0]), '_x setvariable 2;')
        self.assertEqual(str(result[1]), '_y setvariable 3;')

    def test_analyse_assigment1(self):
        test = "_x setvariable 2;"
        result = parse(test)
        self.assertTrue(isinstance(result[0][0], AssignmentStatement))

    def test_analyse_assigment2(self):
        test = '_h = _civs spawn _fPscareC;'
        result = parse(test)
        self.assertTrue(isinstance(result[0][0], AssignmentStatement))
        self.assertEqual('_h = _civs spawn _fPscareC', str(result[0][0]))

    def test_analyse_logical(self):
        test = "_x = (_y == 2);"
        result = parse(test)
        self.assertTrue(isinstance(result[0][0][2][0], LogicalStatement))

    def test_two_statements_bracketed(self):
        result = parse('{_x setvariable 2; _y setvariable 3;};')

        self.assertEqual('{_x setvariable 2; _y setvariable 3;};',
                         str(result))

        self.assertEqual(len(result), 1)

        self.assertEqual(len(result[0]), 2)

        self.assertEqual(len(result[0][0][0]), 2)
        self.assertEqual(len(result[0][0][1]), 2)

    def test_bla(self):
        test = 'if (_n == 1) then {"Air support called to pull away" SPAWN HINTSAOK;} else ' \
               '{"You have no called air support operating currently" SPAWN HINTSAOK;};'
        result = parse_strings(tokenize(test))
        self.assertTrue(isinstance(result[8], String))
        self.assertTrue(isinstance(result[15], String))

        self.assertEqual(str(parse('_n = "This is bla";')), '_n = "This is bla";')

    def test_string(self):

        self.assertEqual('_a = ((_x == _y) || (_y == _z));',
                         str(parse('_a = ((_x == _y) || (_y == _z));')))

    def test_string1(self):
        with self.assertRaises(Exception):
            parse('{(_a = 2;});')
        with self.assertRaises(Exception):
            parse('({_a = 2);};')

    def test_array(self):
        test = '["AirS", nil];'
        result = parse(test)
        self.assertEqual(str(result[0][0]), '["AirS", nil]')

        test = '["AirS" nil];'
        with self.assertRaises(SyntaxError):
            result = parse(test)

        test = '["AirS", if];'
        with self.assertRaises(NotATypeError):
            result = parse(test)

    def test_string2(self):
        self.assertEqual('if (! isNull _x) then {_x setvariable ["AirS", nil];};',
                         str(parse('if (!isNull _x) then {_x setvariable ["AirS",nil];};')))

    def test_if_statement(self):
        test = "if (_x == 2) then {_x = 1;};"
        result = parse(test)
        self.assertEqual(result[0][0], IfToken)
        self.assertEqual(result[0][2], ThenToken)

        test = "if (_x == 2) {_x = 1;};"
        with self.assertRaises(SyntaxIfThenError):
            parse(test)

        test = "if _x == 2 then {_x = 1;};"
        with self.assertRaises(SyntaxIfThenError):
            parse(test)

        test = "if {_x == 2} then {_x = 1;};"
        with self.assertRaises(SyntaxIfThenError):
            parse(test)

        test = "if {_x == 2} then (_x = 1;);"
        with self.assertRaises(SyntaxIfThenError):
            parse(test)

    def test_if_else_statement(self):
        test = "if (_x == 2) then {_x = 1;} else {_x = 3;};"
        result = parse(test)
        print(result)
        self.assertEqual(IfToken, result[0][0])
        self.assertEqual(ThenToken, result[0][2])
