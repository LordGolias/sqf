from unittest import TestCase

from core.parse_exp import parse_exp, partition
from core.exceptions import SyntaxError, UnbalancedParenthesisSyntaxError, IfThenSyntaxError, WrongTypes
from core.types import String, ForEach, Array, Nil, Comma, Boolean, Nothing, \
    Variable as V, OPERATORS as OP, Number as N
from core.statements import Statement, IfThenStatement
from core.parser import parse, parse_strings, tokenize


class TestExpParser(TestCase):

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
                         parse_exp(test, [OP['='], OP['+'], OP['*']], Statement))


class TestParse(TestCase):

    def test_parse_string(self):
        test = 'if (_n == 1) then {"Air support called to pull away" SPAWN HINTSAOK;} else ' \
               '{"You have no called air support operating currently" SPAWN HINTSAOK;};'
        result = parse_strings(tokenize(test))
        self.assertTrue(isinstance(result[8], String))
        self.assertTrue(isinstance(result[15], String))

        self.assertEqual(str(parse('_n = "This is bla";')), '_n = "This is bla";')

    def test_one(self):
        test = "_x setvariable 2;"
        result = parse(test)
        expected = Statement([V('_x'), OP['setvariable'], N(2)], ending=True)

        self.assertEqual(expected, result)

    def test_one_bracketed(self):
        code = '{_x setvariable 2};'
        result = parse(code)
        self.assertEqual(code, str(result))

        expected = Statement([V('_x'), OP['setvariable'], N(2)], ending=True, parenthesis='{}')
        self.assertEqual(expected, result)

    def test_one_bracketed_2(self):
        result = parse('{_x setvariable 2;}')
        expected = Statement([Statement([V('_x'), OP['setvariable'], N(2)], ending=True)], parenthesis='{}')
        self.assertEqual(expected, result)

    def test_parse_bracketed_3(self):
        result = parse('_x = true; _x = false')
        expected = Statement([Statement([V('_x'), OP['='], Boolean(True)], ending=True),
                              Statement([V('_x'), OP['='], Boolean(False)])])
        self.assertEqual(expected, result)

    def test_parse_bracketed_4(self):
        result = parse('_x = true; {_x = false}')
        expected = Statement([Statement([V('_x'), OP['='], Boolean(True)], ending=True),
                              Statement([V('_x'), OP['='], Boolean(False)], parenthesis='{}')])
        self.assertEqual(expected, result)

    def test_two(self):
        result = parse('_x setvariable 2; _y setvariable 3;')
        expected = Statement([Statement([V('_x'), OP['setvariable'], N(2)], ending=True),
                              Statement([V('_y'), OP['setvariable'], N(3)], ending=True)])

        self.assertEqual(expected, result)

    def test_two_bracketed(self):
        result = parse('{_x setvariable 2; _y setvariable 3;};')

        expected = Statement([Statement([V('_x'), OP['setvariable'], N(2)], ending=True),
                              Statement([V('_y'), OP['setvariable'], N(3)], ending=True)],
                             parenthesis='{}', ending=True)

        self.assertEqual(expected, result)

    def test_one_with_parenthesis(self):
        test = "_x = (_y == 2);"
        result = parse(test)

        s1 = Statement([V('_y'), OP['=='], N(2)], parenthesis='()')
        expected = Statement([V('_x'), OP['='], s1], ending=True)

        self.assertEqual(expected, result)

    def test_no_open_parenthesis(self):
        with self.assertRaises(UnbalancedParenthesisSyntaxError):
            parse('_a = x + 2)')
        with self.assertRaises(UnbalancedParenthesisSyntaxError):
            parse('_a = x + 2}')
        with self.assertRaises(UnbalancedParenthesisSyntaxError):
            parse('_a = x + 2]')

    def test_no_close_parenthesis(self):
        with self.assertRaises(UnbalancedParenthesisSyntaxError):
            parse('_a = (x + 2')

    def test_wrong_parenthesis(self):
        with self.assertRaises(Exception):
            parse('{(_a = 2;});')
        with self.assertRaises(Exception):
            parse('({_a = 2);};')

    def test_analyse_expression(self):
        test = '_h = _civs spawn _fPscareC;'
        result = parse(test)
        expected = Statement([V('_h'), OP['='],
                              Statement([V('_civs'), OP['spawn'], V('_fPscareC')])], ending=True)

        self.assertEqual(expected, result)

    def test_analyse_expression2(self):
        test = 'isNil{_x getvariable "AirS"}'
        result = parse(test)
        expected = Statement([OP['isNil'], Statement([V('_x'), OP['getvariable'], String('AirS')], parenthesis='{}')])

        self.assertEqual(expected, result)

    def test_random(self):

        test = """
            _n = 0;
            {
            if (!isNil{_x getvariable "AirS"} && {{alive _x} count units _x > 0}) then {
            _nul = [_x, (getmarkerpos "WestChopStart"),5] SPAWN FUNKTIO_MAD;
            if (!isNull _x) then {_x setvariable ["AirS",nil];};
            _n = 1;
            };
            sleep 0.1;
            } foreach allgroups;
            """

        result = parse(test)

        self.assertEqual(2, len(result))
        self.assertEqual(Statement([V('_n'), OP['='], N(0)], ending=True), result[0])
        self.assertEqual(ForEach, result[1][1])
        self.assertEqual('{}', result[1][0].parenthesis)
        self.assertEqual('{}', result[1][0].parenthesis)
        self.assertTrue(isinstance(result[1][0][0], IfThenStatement))

        # '!isNil{_x getvariable "AirS"} && {{alive _x} count units _x > 0}'
        cond = result[1][0][0]._condition
        expected0 = Statement([OP['!'],
                                    Statement([OP['isNil'],
                                               Statement([V('_x'), OP['getvariable'], String('AirS')],
                                                         parenthesis='{}')])
                                    ])
        expected2 = Statement([Statement([OP['alive'], V('_x')], parenthesis='{}'),
                              OP['count'], Statement([
                                  Statement([OP['units'], V('_x')]), OP['>'], N(0)])
                              ], parenthesis='{}')

        expected = Statement([expected0, OP['&&'], expected2], parenthesis='()')
        self.assertEqual(expected, cond)

        outcome = result[1][0][0]._outcome
        # _nul = [_x, (getmarkerpos "WestChopStart"),5] SPAWN FUNKTIO_MAD;
        expected0 = Statement([V('_nul'), OP['='],
                               Statement([Array([V('_x'),
                                                  Statement([OP['getmarkerpos'], String('WestChopStart')], parenthesis='()'),
                                                  N(5)]),
                                          OP['SPAWN'], V('FUNKTIO_MAD')])
                               ], ending=True)
        self.assertEqual(expected0, outcome[0])

        # if (!isNull _x) then {_x setvariable ["AirS",nil];};
        expected1 = IfThenStatement(Statement([OP['!'], Statement([OP['isNull'], V('_x')])], parenthesis='()'),
                                    Statement([Statement(
                                        [V('_x'), OP['setvariable'], Array([String("AirS"), Nil])],
                                        ending=True)], parenthesis='{}'),
                                    ending=True)

        self.assertEqual(expected1, outcome[1])


class TestParseArray(TestCase):

    def test_array(self):
        test = '["AirS", nil];'
        result = parse(test)
        expected = Statement([Array([String('AirS'), Nil])], ending=True)

        self.assertEqual(expected, result)

        test = '["AirS" nil];'
        with self.assertRaises(SyntaxError):
            parse(test)

        with self.assertRaises(SyntaxError):
            Array([String('AirS'), Comma, Nil])


class TestIfThenStatement(TestCase):

    def test_if_statement(self):
        test = "if (_x == 2) then {_x = 1;};"
        result = parse(test)
        condition = Statement([V('_x'), OP['=='], N(2)], parenthesis='()')
        outcome = Statement([Statement([V('_x'), OP['='], N(1)], ending=True)], parenthesis='{}')
        expected = IfThenStatement(condition, outcome, ending=True)
        self.assertEqual(expected, result)

        test += ' _y = 4;'
        result = parse(test)

        expected = Statement([IfThenStatement(condition, outcome, ending=True),
                              Statement([V('_y'), OP['='], N(4)], ending=True)])
        self.assertEqual(expected, result)

    def test_if_syntax(self):
        test = "if (_x == 2) {_x = 1;};"
        with self.assertRaises(IfThenSyntaxError):
            parse(test)

        test = "if _x == 2 then {_x = 1;};"
        with self.assertRaises(IfThenSyntaxError):
            parse(test)

        test = "if {_x == 2} then {_x = 1;};"
        with self.assertRaises(IfThenSyntaxError):
            parse(test)

        test = "if {_x == 2} then (_x = 1;);"
        with self.assertRaises(IfThenSyntaxError):
            parse(test)

    def test_if_with_extra(self):
        test = "if (_x == 2) then {_x = 1;}; _y = 4;"
        result = parse(test)
        condition = Statement([V('_x'), OP['=='], N(2)], parenthesis='()')
        outcome = Statement([Statement([V('_x'), OP['='], N(1)], ending=True)], parenthesis='{}')
        expected = Statement([IfThenStatement(condition, outcome, ending=True),
                              Statement([V('_y'), OP['='], N(4)], ending=True)])
        self.assertEqual(expected, result)

    def test_if_else_statement(self):
        test = "if (_x == 2) then {_x = 1;} else {_x = 3;};"
        result = parse(test)

        condition = Statement([V('_x'), OP['=='], N(2)], parenthesis='()')
        outcome = Statement([Statement([V('_x'), OP['='], N(1)], ending=True)], parenthesis='{}')
        _else = Statement([Statement([V('_x'), OP['='], N(3)], ending=True)], parenthesis='{}')

        expected = IfThenStatement(condition, outcome, _else, ending=True)
        self.assertEqual(expected, result)

        test += " _y = 4;"
        result = parse(test)
        expected = Statement([expected, Statement([V('_y'), OP['='], N(4)], ending=True)])

        self.assertEqual(expected, result)

    # def test_assign_if(self):
    #     test = '_x = if (_x == 2) then {1} else {3};'
    #     result = parse(test)
    #
    #     self.assertEqual(V('_x'), result[0])
    #     self.assertTrue(isinstance(result[2], IfThenStatement))

    def test_wrong_if(self):
        with self.assertRaises(IfThenSyntaxError):
            parse('if (_x == 2) then {_x = 1;} else {_x = 3;} = 2')

        with self.assertRaises(IfThenSyntaxError):
            parse('if (_x == 2) then {_x = 1;} = 2')
