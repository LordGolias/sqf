from unittest import TestCase

from arma3.parse_exp import parse_exp, partition
from arma3.exceptions import SyntaxError, UnbalancedParenthesisSyntaxError
from arma3.types import String, Statement, Code, Array, Boolean, Variable as V, \
    Number as N
from arma3.keywords import Keyword, Nil, Comma, IfToken, ThenToken
from arma3.parser_types import Comment, Space, EndOfLine
from arma3.parser import parse, parse_strings
from arma3.base_tokenizer import tokenize


class TestExpParser(TestCase):

    def test_partition(self):
        res = partition([V('_x'), Keyword('='), V('2')], Keyword('='))
        self.assertEqual([[V('_x')], Keyword('='), [V('2')]], res)

    def test_binary(self):
        # a=b
        test = [V('a'), Keyword('='), V('b')]
        self.assertEqual([V('a'), Keyword('='), V('b')], parse_exp(test, [Keyword('=')]))

        # a=b+c*d
        test = [V('a'), Keyword('='), V('b'), Keyword('+'), V('c'), Keyword('*'), V('d')]
        self.assertEqual([V('a'), Keyword('='), [V('b'), Keyword('+'), [V('c'), Keyword('*'), V('d')]]],
                         parse_exp(test, [Keyword('='), Keyword('+'), Keyword('*')]))

    def test_binary_two_same_operators(self):
        # a=b=e+c*d
        test = [V('a'), Keyword('='), V('b'), Keyword('='), V('e'), Keyword('+'), V('c'), Keyword('*'), V('d')]
        self.assertEqual([V('a'), Keyword('='), [V('b'), Keyword('='), [V('e'), Keyword('+'), [V('c'), Keyword('*'), V('d')]]]],
                         parse_exp(test, [Keyword('='), Keyword('+'), Keyword('*')]))

        # a+b+c
        test = [V('a'), Keyword('+'), V('b'), Keyword('+'), V('c')]
        self.assertEqual([V('a'), Keyword('+'), [V('b'), Keyword('+'), V('c')]],
                         parse_exp(test, [Keyword('='), Keyword('+'), Keyword('*')]))

    def test_binary_order_matters(self):
        # a+b=c
        test = [V('a'), Keyword('+'), V('b'), Keyword('='), V('c')]
        self.assertEqual([[V('a'), Keyword('+'), V('b')], Keyword('='), V('c')],
                         parse_exp(test, [Keyword('='), Keyword('+'), Keyword('*')]))

    def test_unary(self):
        # a=!b||c
        test = [V('a'), Keyword('='), Keyword('!'), V('b'), Keyword('||'), V('c')]
        self.assertEqual([V('a'), Keyword('='), [[Keyword('!'), V('b')], Keyword('||'), V('c')]],
                         parse_exp(test, [Keyword('='), Keyword('||'), Keyword('!')]))

    def test_with_statement(self):
        test = [V('a'), Keyword('+'), V('b'), Keyword('='), V('c')]
        self.assertEqual(Statement([Statement([V('a'), Keyword('+'), V('b')]), Keyword('='), V('c')]),
                         parse_exp(test, [Keyword('='), Keyword('+'), Keyword('*')], Statement))


class ParserTestCase(TestCase):
    
    def assertEqualStatement(self, expected, result, code):
        self.assertEqual(expected, result)
        self.assertEqual(code, str(result))


class ParseCode(ParserTestCase):

    def test_parse_string(self):
        test = 'if (_n == 1) then {"Air support called to pull away" SPAWN HINTSAOK;} else ' \
               '{"You have no called air support operating currently" SPAWN HINTSAOK;};'
        result = parse_strings(tokenize(test))
        self.assertTrue(isinstance(result[13], String))
        self.assertTrue(isinstance(result[24], String))

        self.assertEqual(str(parse('_n = "This is bla";')), '_n = "This is bla";')

    def test_one(self):
        code = '_x=2;'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='), N(2)], ending=True)])

        self.assertEqualStatement(expected, result, code)

    def test_one_bracketed(self):
        code = '{_x="AirS";}'
        result = parse(code)
        expected = Statement([Statement([Code([Statement([V('_x'), Keyword('='), String('AirS')], ending=True)])])])
        
        self.assertEqualStatement(expected, result, code)

    def test_not_delayed(self):
        code = '(_x="AirS";)'
        result = parse(code)
        expected = Statement([Statement([
            Statement([V('_x'), Keyword('='), String('AirS')], ending=True)], parenthesis=True)])
        
        self.assertEqualStatement(expected, result, code)

        code = '(_x="AirS";);'
        result = parse(code)
        expected = Statement([Statement([Statement([V('_x'), Keyword('='), String('AirS')], ending=True)],
                                        parenthesis=True, ending=True)
                              ])
        self.assertEqualStatement(expected, result, code)

    def test_assign(self):
        code = '_x=(_x=="AirS");'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='),
                              Statement([Statement([V('_x'), Keyword('=='), String('AirS')])], parenthesis=True)], ending=True)])
        self.assertEqualStatement(expected, result, code)

    def test_two_statements(self):
        code = '_x=true;_x=false'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='), Boolean(True)], ending=True),
                              Statement([V('_x'), Keyword('='), Boolean(False)])])

        self.assertEqualStatement(expected, result, code)

    def test_parse_bracketed_4(self):
        code = '_x=true;{_x=false}'
        result = parse(code)
        expected = Statement([
            Statement([V('_x'), Keyword('='), Boolean(True)], ending=True),
            Statement([Code([Statement([V('_x'), Keyword('='), Boolean(False)])])])
        ])

        self.assertEqualStatement(expected, result, code)

    def test_two(self):
        code = '_x=2;_y=3;'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='), N(2)], ending=True),
                         Statement([V('_y'), Keyword('='), N(3)], ending=True)])

        self.assertEqualStatement(expected, result, code)

    def test_two_bracketed(self):
        code = '{_x=2;_y=3;};'
        result = parse(code)
        expected = Statement([Statement([Code([
            Statement([V('_x'), Keyword('='), N(2)], ending=True),
            Statement([V('_y'), Keyword('='), N(3)], ending=True)])], ending=True)])

        self.assertEqualStatement(expected, result, code)

    def test_assign_with_parenthesis(self):
        code = "_x=(_y==2);"
        result = parse(code)

        s1 = Statement([V('_y'), Keyword('=='), N(2)])
        expected = Statement([Statement([V('_x'), Keyword('='), Statement([s1], parenthesis=True)], ending=True)])

        self.assertEqualStatement(expected, result, code)

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
        code = '_h = _civs spawn _fPscareC;'
        result = parse(code)
        expected = Statement([Statement([
            Statement([V('_h'), Space()]),
            Keyword('='),
            Statement([
                Statement([Space(), V('_civs'), Space()]),
                Keyword('spawn'),
                Statement([Space(), V('_fPscareC')])
            ])], ending=True)])

        self.assertEqualStatement(expected, result, code)

    def test_analyse_expression2(self):
        code = 'isNil{_x getVariable "AirS"}'
        result = parse(code)
        expected = Statement([Statement([
            Keyword('isNil'),
            Code([Statement([
                Statement([V('_x'), Space()]),
                Keyword('getVariable'),
                Statement([Space(), String('AirS')])])])
            ])])
        
        self.assertEqualStatement(expected, result, code)

    def test_code(self):
        code = '_is1={_x==1};'
        result = parse(code)
        expected = Statement([Statement([V('_is1'), Keyword('='),
                                         Code([Statement([V('_x'), Keyword('=='), N(1)])])], ending=True)])
        
        self.assertEqualStatement(expected, result, code)

    def test_if_then(self):
        code = 'if(true)then{private"_x";_x}'
        result = parse(code)
        expected = Statement([Statement([IfToken, Statement([Statement([Boolean(True)])], parenthesis=True),
                                         ThenToken, Code([
                Statement([Keyword('private'), String('_x')], ending=True),
                Statement([V('_x')])])
        ])])
        
        self.assertEqualStatement(expected, result, code)


class ParseArray(ParserTestCase):

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
        code = '[];'
        result = parse(code)
        expected = Statement([Statement([Array([Statement([])])], ending=True)])

        self.assertEqualStatement(expected, result, code)

    def test_parse_3(self):
        code = '[1, 2, 3]'
        result = parse(code)
        expected = Statement([Statement([
            Array([Statement([N(1)]), Statement([Space(), N(2)]), Statement([Space(), N(3)])])
        ])])

        self.assertEqual(expected, result, code)


class ParseLineComments(ParserTestCase):

    def test_inline(self):
        code = '_x = 2 // the two'
        result = parse(code)
        expected = Statement([Statement([
            Statement([V('_x'), Space()]),
            Keyword('='),
            Statement([Space(), N(2), Space(), Comment('// the two')])])
        ])

        self.assertEqualStatement(expected, result, code)

    def test_inline_no_eof(self):
        code = '_x = 2; // the two'
        result = parse(code)
        expected = Statement([Statement([
            Statement([V('_x'), Space()]),
            Keyword('='),
            Statement([Space(), N(2)])], ending=True),
            Statement([Space(), Comment('// the two')])
        ])

        self.assertEqualStatement(expected, result, code)

    def test_inline_with_eol(self):
        code = '_x=2;// the two\n_x=3;'
        result = parse(code)
        expected = Statement([
            Statement([V('_x'), Keyword('='), N(2)], ending=True),
            Statement([Statement([Comment('// the two\n'), V('_x')]), Keyword('='), N(3)], ending=True)])

        self.assertEqualStatement(expected, result, code)


class ParseBlockComments(ParserTestCase):

    def test_inline(self):
        code = '_x=2/* the two */'
        result = parse(code)
        expected = Statement([Statement([
            V('_x'),
            Keyword('='),
            Statement([N(2), Comment('/* the two */')])])])

        self.assertEqualStatement(expected, result, code)

    def test_with_lines(self):
        code = '_x=2;/* the two \n the three\n the four\n */\n_x=3'
        result = parse(code)
        expected = Statement([Statement([
            V('_x'),
            Keyword('='),
            N(2)], ending=True),
            Statement([Statement([Comment('/* the two \n the three\n the four\n */'),
                                  EndOfLine(), V('_x')]), Keyword('='), N(3)])
        ])

        self.assertEqualStatement(expected, result, code)

    def test_with_other_comment(self):
        code = '_x=2;/* // two four\n */\n_x=3'
        result = parse(code)
        expected = Statement([Statement([
            V('_x'),
            Keyword('='),
            N(2)], ending=True),
            Statement(
                [Statement([Comment('/* // two four\n */'), EndOfLine(), V('_x')]), Keyword('='), N(3)])
        ])

        self.assertEqualStatement(expected, result, code)
