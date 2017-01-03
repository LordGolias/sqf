from unittest import TestCase

from arma3.parse_exp import parse_exp, partition
from arma3.exceptions import SyntaxError, UnbalancedParenthesisSyntaxError
from arma3.types import String, Statement, Code, Array, Nil, Comma, IfToken, ThenToken, Boolean, Variable as V, \
    Number as N
from arma3.parser_types import Comment, Space, EndOfLine
from arma3.operators import OPERATORS as OP
from arma3.parser import parse, parse_strings, tokenize
from arma3.base_tokenizer import tokenize



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

    def test_tokenize(self):
        x = tokenize('/*_x = (1 + 2);*/')
        print(x)

    def test_parse_string(self):
        test = 'if (_n == 1) then {"Air support called to pull away" SPAWN HINTSAOK;} else ' \
               '{"You have no called air support operating currently" SPAWN HINTSAOK;};'
        result = parse_strings(tokenize(test))
        self.assertTrue(isinstance(result[13], String))
        self.assertTrue(isinstance(result[24], String))

        self.assertEqual(str(parse('_n = "This is bla";')), '_n = "This is bla";')

    def test_one(self):
        result = parse('_x=2;')
        expected = Statement([Statement([V('_x'), OP['='], N(2)], ending=True)])

        self.assertEqual(expected, result)

    def test_one_bracketed(self):
        result = parse('{_x="AirS";}')
        expected = Statement([Statement([Code([Statement([V('_x'), OP['='], String('AirS')], ending=True)])])])
        self.assertEqual(expected, result)

    def test_not_delayed(self):
        result = parse('(_x="AirS";)')
        expected = Statement([Statement([
            Statement([V('_x'), OP['='], String('AirS')], ending=True)], parenthesis=True)])
        self.assertEqual(expected, result)

        result = parse('(_x="AirS";);')
        expected = Statement([Statement([Statement([V('_x'), OP['='], String('AirS')], ending=True)],
                                        parenthesis=True, ending=True)
                              ])
        self.assertEqual(expected, result)

    def test_assign(self):
        result = parse('_x=(_x=="AirS");')
        expected = Statement([Statement([V('_x'), OP['='],
                              Statement([Statement([V('_x'), OP['=='], String('AirS')])], parenthesis=True)], ending=True)])
        self.assertEqual(expected, result)

    def test_two_statements(self):
        result = parse('_x=true;_x=false')
        expected = Statement([Statement([V('_x'), OP['='], Boolean(True)], ending=True),
                              Statement([V('_x'), OP['='], Boolean(False)])])
        self.assertEqual(expected, result)

    def test_parse_bracketed_4(self):
        result = parse('_x=true;{_x=false}')
        expected = Statement([
            Statement([V('_x'), OP['='], Boolean(True)], ending=True),
            Statement([Code([Statement([V('_x'), OP['='], Boolean(False)])])])
        ])
        self.assertEqual(expected, result)

    def test_two(self):
        result = parse('_x=2;_y=3;')
        expected = Statement([Statement([V('_x'), OP['='], N(2)], ending=True),
                         Statement([V('_y'), OP['='], N(3)], ending=True)])

        self.assertEqual(expected, result)

    def test_two_bracketed(self):
        result = parse('{_x=2;_y=3;};')

        expected = Statement([Statement([Code([
            Statement([V('_x'), OP['='], N(2)], ending=True),
            Statement([V('_y'), OP['='], N(3)], ending=True)])], ending=True)])

        self.assertEqual(expected, result)

    def test_assign_with_parenthesis(self):
        test = "_x=(_y==2);"
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
        expected = Statement([Statement([
            Statement([V('_h'), Space()]),
            OP['='],
            Statement([
                Statement([Space(), V('_civs'), Space()]),
                OP['spawn'],
                Statement([Space(), V('_fPscareC')])
            ])], ending=True)])

        self.assertEqual(expected, result)

    def test_analyse_expression2(self):
        test = 'isNil{_x getVariable "AirS"}'
        result = parse(test)
        expected = Statement([Statement([
            OP['isNil'],
            Code([Statement([
                Statement([V('_x'), Space()]),
                OP['getVariable'],
                Statement([Space(), String('AirS')])])])
            ])])
        self.assertEqual(expected, result)

    def test_code(self):
        result = parse('_is1={_x==1};')
        expected = Statement([Statement([V('_is1'), OP['='],
                                         Code([Statement([V('_x'), OP['=='], N(1)])])], ending=True)])
        self.assertEqual(expected, result)

    def test_if_then(self):
        result = parse('if(true)then{private"_x";_x}')
        expected = Statement([Statement([IfToken, Statement([Statement([Boolean(True)])], parenthesis=True),
                                         ThenToken, Code([
                Statement([OP['private'], String('_x')], ending=True),
                Statement([V('_x')])])
        ])])
        self.assertEqual(expected, result)


class ParseArray(TestCase):

    def test_basic(self):
        test = '["AirS", nil];'
        result = parse(test)
        expected = Statement([Statement([
            Array([Statement([String('AirS')]), Statement([Space(), Nil])])], ending=True)])

        self.assertEqual(expected, result)

    def test_exceptions(self):
        with self.assertRaises(SyntaxError):
            Array([String('AirS'), Comma, Nil])

        with self.assertRaises(SyntaxError):
            parse('["AirS"; nil];')

        with self.assertRaises(SyntaxError):
            parse('[,];')

        with self.assertRaises(SyntaxError):
            parse('["AirS",];')

        with self.assertRaises(SyntaxError):
            parse('[nil,,nil];')

    def test_empty(self):
        result = parse('[];')
        expected = Statement([Statement([Array([Statement([])])], ending=True)])
        self.assertEqual(expected, result)

    def test_parse_3(self):
        result = parse('[1, 2, 3]')
        expected = Statement([Statement([
            Array([Statement([N(1)]), Statement([Space(), N(2)]), Statement([Space(), N(3)])])
        ])])
        self.assertEqual(expected, result)


class ParseLineComments(TestCase):

    def test_inline(self):
        result = parse('_x = 2 // the two')
        expected = Statement([Statement([
            Statement([V('_x'), Space()]),
            OP['='],
            Statement([Space(), N(2), Space(), Comment('// the two')])])
        ])

        self.assertEqual(expected, result)
        self.assertEqual(str(expected), str(result))

    def test_inline_no_eof(self):
        result = parse('_x = 2; // the two')
        expected = Statement([Statement([
            Statement([V('_x'), Space()]),
            OP['='],
            Statement([Space(), N(2)])], ending=True),
            Statement([Space(), Comment('// the two')])
        ])

        self.assertEqual(expected, result)

    def test_inline_with_eol(self):
        result = parse('_x=2;// the two\n_x=3;')
        expected = Statement([
            Statement([V('_x'), OP['='], N(2)], ending=True),
            Statement([Statement([Comment('// the two\n'), V('_x')]), OP['='], N(3)], ending=True)])

        self.assertEqual(expected, result)
        self.assertEqual(str(expected), str(result))


class ParseBlockComments(TestCase):

    def test_inline(self):
        result = parse('_x=2/* the two */')
        expected = Statement([Statement([
            V('_x'),
            OP['='],
            Statement([N(2), Comment('/* the two */')])])])

        self.assertEqual(expected, result)
        self.assertEqual(str(expected), str(result))

    def test_with_lines(self):
        result = parse('_x=2;/* the two \n the three\n the four\n */\n_x=3')
        expected = Statement([Statement([
            V('_x'),
            OP['='],
            N(2)], ending=True),
            Statement([Statement([Comment('/* the two \n the three\n the four\n */'),
                                  EndOfLine(), V('_x')]), OP['='], N(3)])
        ])

        self.assertEqual(expected, result)
        self.assertEqual(str(expected), str(result))

    def test_with_other_comment(self):
        result = parse('_x=2;/* // two four\n */\n_x=3')
        expected = Statement([Statement([
            V('_x'),
            OP['='],
            N(2)], ending=True),
            Statement(
                [Statement([Comment('/* // two four\n */'), EndOfLine(), V('_x')]), OP['='], N(3)])
        ])

        self.assertEqual(expected, result)
        self.assertEqual(str(expected), str(result))
