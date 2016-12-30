from unittest import TestCase

from core.parse_exp import parse_exp, partition
from core.exceptions import SyntaxError, UnbalancedParenthesisSyntaxError
from core.types import String, Statement, Code, Array, Nil, Comma, IfToken, ThenToken, Boolean, Variable as V, Number as N
from core.operators import OPERATORS as OP
from core.parser import parse, parse_strings, tokenize


class TestExpParser(TestCase):

    def test_partition(self):
        res = partition([V('_x'), OP['='], V('2')], OP['='])
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
        test = [V('a'), OP['+'], V('b'), OP['='], V('c')]
        self.assertEqual(Statement([Statement([V('a'), OP['+'], V('b')]), OP['='], V('c')]),
                         parse_exp(test, [OP['='], OP['+'], OP['*']], Statement))


class ParseCode(TestCase):

    def test_parse_string(self):
        test = 'if (_n == 1) then {"Air support called to pull away" SPAWN HINTSAOK;} else ' \
               '{"You have no called air support operating currently" SPAWN HINTSAOK;};'
        result = parse_strings(tokenize(test))
        self.assertTrue(isinstance(result[8], String))
        self.assertTrue(isinstance(result[15], String))

        self.assertEqual(str(parse('_n = "This is bla";')), '_n = "This is bla";')

    def test_one(self):
        result = parse('_x = 2;')
        expected = Statement([Statement([V('_x'), OP['='], N(2)], ending=True)])

        self.assertEqual(expected, result)

    def test_one_bracketed(self):
        result = parse('{_x = "AirS";}')
        expected = Statement([Statement([Code([Statement([V('_x'), OP['='], String('AirS')], ending=True)])])])
        self.assertEqual(expected, result)

    def test_not_delayed(self):
        result = parse('(_x = "AirS";)')
        expected = Statement([Statement([
            Statement([V('_x'), OP['='], String('AirS')], ending=True)], parenthesis=True)])
        self.assertEqual(expected, result)

        result = parse('(_x = "AirS";);')
        expected = Statement([Statement([Statement([V('_x'), OP['='], String('AirS')], ending=True)],
                                        parenthesis=True, ending=True)
                              ])
        self.assertEqual(expected, result)

    def test_assign(self):
        result = parse('_x = (_x == "AirS");')
        expected = Statement([Statement([V('_x'), OP['='],
                              Statement([Statement([V('_x'), OP['=='], String('AirS')])], parenthesis=True)], ending=True)])
        self.assertEqual(expected, result)

    def test_two_statements(self):
        result = parse('_x = true; _x = false')
        expected = Statement([Statement([V('_x'), OP['='], Boolean(True)], ending=True),
                              Statement([V('_x'), OP['='], Boolean(False)])])
        self.assertEqual(expected, result)

    def test_parse_bracketed_4(self):
        result = parse('_x = true; {_x = false}')
        expected = Statement([
            Statement([V('_x'), OP['='], Boolean(True)], ending=True),
            Statement([Code([Statement([V('_x'), OP['='], Boolean(False)])])])
        ])
        self.assertEqual(expected, result)

    def test_two(self):
        result = parse('_x setvariable 2; _y setvariable 3;')
        expected = Statement([Statement([V('_x'), OP['setvariable'], N(2)], ending=True),
                         Statement([V('_y'), OP['setvariable'], N(3)], ending=True)])

        self.assertEqual(expected, result)

    def test_two_bracketed(self):
        result = parse('{_x setvariable 2; _y setvariable 3;};')

        expected = Statement([Statement([Code([
            Statement([V('_x'), OP['setvariable'], N(2)], ending=True),
            Statement([V('_y'), OP['setvariable'], N(3)], ending=True)])], ending=True)])

        self.assertEqual(expected, result)

    def test_assign_with_parenthesis(self):
        test = "_x = (_y == 2);"
        result = parse(test)

        s1 = Statement([V('_y'), OP['=='], N(2)])
        expected = Statement([Statement([V('_x'), OP['='], Statement([s1], parenthesis=True)], ending=True)])

        self.assertEqual(expected, result)

    def test_no_open_parenthesis(self):
        with self.assertRaises(UnbalancedParenthesisSyntaxError):
            parse('_a = x + 2)')
        with self.assertRaises(UnbalancedParenthesisSyntaxError):
            parse('_a = x + 2}')
        with self.assertRaises(UnbalancedParenthesisSyntaxError):
            parse('_a = x + 2]')

    def test_wrong_parenthesis(self):
        with self.assertRaises(Exception):
            parse('{(_a = 2;});')
        with self.assertRaises(Exception):
            parse('({_a = 2);};')

    def test_no_close_parenthesis(self):
        with self.assertRaises(UnbalancedParenthesisSyntaxError):
            parse('_a = (x + 2')

    def test_analyse_expression(self):
        test = '_h = _civs spawn _fPscareC;'
        result = parse(test)
        expected = Statement([Statement([V('_h'), OP['='],
                              Statement([V('_civs'), OP['spawn'], V('_fPscareC')])], ending=True)])

        self.assertEqual(expected, result)

    def test_analyse_expression2(self):
        test = 'isNil{_x getvariable "AirS"}'
        result = parse(test)
        expected = Statement([Statement([OP['isNil'],
                                         Code([Statement([V('_x'), OP['getvariable'], String('AirS')])])
                                         ])
                              ])
        self.assertEqual(expected, result)

    def test_array(self):
        test = '["AirS", nil];'
        result = parse(test)
        expected = Statement([Statement([Array([String('AirS'), Nil])], ending=True)])

        self.assertEqual(expected, result)

        with self.assertRaises(SyntaxError):
            parse('["AirS" nil];')

        with self.assertRaises(SyntaxError):
            Array([String('AirS'), Comma, Nil])

        with self.assertRaises(SyntaxError):
            parse('["AirS"; nil];')

        result = parse('[];')
        expected = Statement([Statement([Array([])], ending=True)])
        self.assertEqual(expected, result)

    def test_code(self):
        result = parse('_is1 = {_x == 1};')
        expected = Statement([Statement([V('_is1'), OP['='],
                                         Code([Statement([V('_x'), OP['=='], N(1)])])], ending=True)])
        self.assertEqual(expected, result)

    def test_if_then(self):
        result = parse('if (true) then {private "_x"; _x}')
        expected = Statement([Statement([IfToken, Statement([Statement([Boolean(True)])], parenthesis=True),
                                         ThenToken, Code([
                Statement([OP['private'], String('_x')], ending=True),
                Statement([V('_x')])])
        ])])
        self.assertEqual(expected, result)
