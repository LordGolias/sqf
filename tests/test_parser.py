from unittest import TestCase

from sqf.parse_exp import parse_exp, partition
from sqf.exceptions import SQFError, SQFParenthesisError, SQFParserError
from sqf.types import String, Statement, Code, Array, Boolean, Variable as V, \
    Number as N
from sqf.keywords import Keyword
from sqf.parser_types import Comment, Space, EndOfLine
from sqf.parser import parse, parse_strings, identify_token
from sqf.base_tokenizer import tokenize


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
        code = 'if (_n == 1) then {"Air support called to pull away" SPAWN HINTSAOK;} else ' \
               '{"You have no called air support operating currently" SPAWN HINTSAOK;};'
        result = parse_strings(tokenize(code), identify_token)
        self.assertTrue(isinstance(result[13], String))
        self.assertTrue(isinstance(result[24], String))

        self.assertEqual(str(parse('_n = "This is bla";')), '_n = "This is bla";')

    def test_parse_double_quote(self):
        code = '_string = "my string ""with"" quotes"'
        result = parse_strings(tokenize(code), identify_token)
        self.assertTrue(isinstance(result[4], String))
        self.assertEqual('my string ""with"" quotes', result[4].value)

    def test_parse_empty_string(self):
        code = '_string = ""'
        result = parse_strings(tokenize(code), identify_token)
        self.assertTrue(isinstance(result[4], String))
        self.assertEqual('', result[4].value)

    def test_one(self):
        code = '_x=2;'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='), N(2)], ending=True)])

        self.assertEqualStatement(expected, result, code)

    def test_one_bracketed(self):
        code = '{_x="AirS";}'
        result = parse(code)
        expected = Statement([Statement([Code([Statement([V('_x'), Keyword('='), String('"AirS"')], ending=True)])])])
        
        self.assertEqualStatement(expected, result, code)

    def test_not_delayed(self):
        code = '(_x="AirS";)'
        result = parse(code)
        expected = Statement([Statement([
            Statement([V('_x'), Keyword('='), String('"AirS"')], ending=True)], parenthesis=True)])
        
        self.assertEqualStatement(expected, result, code)

        code = '(_x="AirS";);'
        result = parse(code)
        expected = Statement([Statement([Statement([V('_x'), Keyword('='), String('"AirS"')], ending=True)],
                                        parenthesis=True, ending=True)
                              ])
        self.assertEqualStatement(expected, result, code)

    def test_assign(self):
        code = '_x=(_x=="AirS");'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='),
                              Statement([Statement([V('_x'), Keyword('=='), String('"AirS"')])], parenthesis=True)], ending=True)])
        self.assertEqualStatement(expected, result, code)

    def test_assign_array(self):
        code = '_y = [];'
        result = parse(code)
        expected = Statement([Statement([
            Statement([V('_y'), Space()]),
            Keyword('='),
            Statement([Space(), Array([Statement([])])])], ending=True)])
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
        with self.assertRaises(SQFParenthesisError):
            parse('_a = x + 2)')
        with self.assertRaises(SQFParenthesisError):
            parse('_a = x + 2}')
        with self.assertRaises(SQFParenthesisError):
            parse('_a = x + 2]')

    def test_wrong_parenthesis(self):
        with self.assertRaises(Exception):
            parse('{(_a = 2;});')
        with self.assertRaises(Exception):
            parse('({_a = 2);};')

    def test_no_close_parenthesis(self):
        with self.assertRaises(SQFParenthesisError):
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
                Statement([Space(), String('"AirS"')])])])
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
        expected = Statement([Statement([Keyword('if'), Statement([Statement([Boolean(True)])], parenthesis=True),
                                         Keyword('then'), Code([
                Statement([Keyword('private'), String('"_x"')], ending=True),
                Statement([V('_x')])])
        ])])
        
        self.assertEqualStatement(expected, result, code)

    def test_switch(self):
        code = 'switch (0) do'
        result = parse(code)
        expected = Statement([Statement([
            Keyword('switch'),
            Space(),
            Statement([Statement([N(0)])], parenthesis=True),
            Space(),
            Keyword('do')])])
        self.assertEqualStatement(expected, result, code)

    def test_position_statement(self):
        code = 'switch (0) do'
        result = parse(code)
        self.assertEqual((1, 9), result[0][2][0].position)  # the 0 is in column 9

    def test_position_array(self):
        code = 'switch [1,2] do'
        result = parse(code)
        number1 = result[0][2].value[0][0]
        number2 = result[0][2].value[1][0]
        assert (number1 == N(1))
        assert (number2 == N(2))
        self.assertEqual((1, 9), number1.position)
        self.assertEqual((1, 11), number2.position)

    def test_position(self):
        code = '_x=2 _y=3;'
        result = parse(code)
        self.assertEqual(result[0][1].position, (1, 3))


class ParseArray(ParserTestCase):

    def test_basic(self):
        test = '["AirS", nil];'
        result = parse(test)
        expected = Statement([Statement([
            Array([Statement([String('"AirS"')]), Statement([Space(), Keyword('nil')])])], ending=True)])

        self.assertEqual(expected, result)

    def test_exceptions(self):
        with self.assertRaises(SQFError):
            Array([String('"AirS"'), Keyword(','), Keyword('nil')])

        with self.assertRaises(SQFParserError):
            parse('["AirS"; nil];')

        with self.assertRaises(SQFParserError):
            parse('[,];')

        with self.assertRaises(SQFParserError):
            parse('["AirS",];')

        with self.assertRaises(SQFParserError):
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


class ParseStrings(ParserTestCase):

    def test_single_double(self):
        code = '_x=\'"1"\''
        result = parse(code)
        self.assertEqual(str(result[0][2]), "'\"1\"'")

    def test_double_single(self):
        code = '_x="\'1\'"'
        result = parse(code)
        self.assertEqual(str(result[0][2]), "\"'1'\"")

    def test_double_escape(self):
        code = '_x="""1"""'
        result = parse(code)
        self.assertEqual(str(result[0][2]), '"""1"""')

    def test_single_escape(self):
        code = "_x='''1'''"
        result = parse(code)
        self.assertEqual(str(result[0][2]), "'''1'''")

    def test_error(self):
        code = "_x='1111"
        with self.assertRaises(Exception) as cm:
            parse(code)
        self.assertEqual((1, 4), cm.exception.position)
