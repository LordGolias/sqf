from unittest import TestCase

from sqf.base_type import get_coord
from sqf.parse_exp import parse_exp, partition
from sqf.exceptions import SQFError, SQFParenthesisError, SQFParserError
from sqf.types import String, Statement, Code, Array, Boolean, Variable as V, \
    Number as N, BaseTypeContainer
from sqf.keywords import Keyword, KeywordControl, KeywordConstant
from sqf.parser_types import Comment, Space, Tab, EndOfLine, BrokenEndOfLine
from sqf.parser import parse, parse_strings, identify_token
from sqf.base_tokenizer import tokenize


def build_indexes(string):
    indexes = {}
    for i in range(len(string)):
        coord = get_coord(string[:i])
        indexes[coord] = i

    return indexes


class Element:
    def __init__(self, string, coordinates):
        self.string = string
        self.coordinates = coordinates

    def __repr__(self):
        return '<%s|%d,%d>' % tuple((self.string,) + self.coordinates)


def _get_elements(statement1):
    positions = []

    for token in statement1._tokens:
        if isinstance(token, BaseTypeContainer):
            positions.append(_get_elements(token))
        else:
            positions.append([Element(str(token), token.position)])

    # flatten
    return [item for sublist in positions for item in sublist]


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
        self.assertCorrectPositions(result, code)

    def assertCorrectPositions(self, result, code):
        indexes = build_indexes(code)
        for element in _get_elements(result):
            index = indexes[element.coordinates]
            lenght = len(element.string)
            self.assertEqual(code[index:index+lenght], element.string)


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

    def test_parse_windows_eol(self):
        code = '_x\r\n'
        result = parse(code)
        expected = Statement([Statement([V('_x'), EndOfLine('\r\n')])])
        self.assertEqualStatement(expected, result, code)

    def test_parse_bool(self):
        code = '_x=true;'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='), Boolean(True)], ending=';')])

        self.assertEqualStatement(expected, result, code)

    def test_parse_tab(self):
        code = '\t_x;'
        result = parse(code)
        expected = Statement([Statement([Tab(), V('_x')], ending=';')])

        self.assertEqualStatement(expected, result, code)

    def test_one(self):
        code = '_x=2;'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='), N(2)], ending=';')])

        self.assertEqualStatement(expected, result, code)

    def test_one_bracketed(self):
        code = '{_x="AirS";}'
        result = parse(code)
        expected = Statement([Statement([Code([Statement([V('_x'), Keyword('='), String('"AirS"')], ending=';')])])])
        
        self.assertEqualStatement(expected, result, code)

    def test_not_delayed(self):
        code = '(_x="AirS";)'
        result = parse(code)
        expected = Statement([Statement([
            Statement([V('_x'), Keyword('='), String('"AirS"')], ending=';')], parenthesis=True)])
        
        self.assertEqualStatement(expected, result, code)

        code = '(_x="AirS";);'
        result = parse(code)
        expected = Statement([Statement([Statement([V('_x'), Keyword('='), String('"AirS"')], ending=';')],
                                        parenthesis=True, ending=';')
                              ])
        self.assertEqualStatement(expected, result, code)

    def test_assign(self):
        code = '_x=(_x=="AirS");'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='),
                              Statement([Statement([V('_x'), Keyword('=='), String('"AirS"')])], parenthesis=True)], ending=';')])
        self.assertEqualStatement(expected, result, code)

    def test_assign_array(self):
        code = '_y = [];'
        result = parse(code)
        expected = Statement([Statement([
            Statement([V('_y'), Space()]),
            Keyword('='),
            Statement([Space(), Array([Statement([])])])], ending=';')])
        self.assertEqualStatement(expected, result, code)

    def test_two_statements(self):
        code = '_x=true;_x=false'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='), Boolean(True)], ending=';'),
                              Statement([V('_x'), Keyword('='), Boolean(False)])])

        self.assertEqualStatement(expected, result, code)

    def test_parse_bracketed_4(self):
        code = '_x=true;{_x=false}'
        result = parse(code)
        expected = Statement([
            Statement([V('_x'), Keyword('='), Boolean(True)], ending=';'),
            Statement([Code([Statement([V('_x'), Keyword('='), Boolean(False)])])])
        ])

        self.assertEqualStatement(expected, result, code)

    def test_two(self):
        code = '_x=2;_y=3;'
        result = parse(code)
        expected = Statement([Statement([V('_x'), Keyword('='), N(2)], ending=';'),
                         Statement([V('_y'), Keyword('='), N(3)], ending=';')])

        self.assertEqualStatement(expected, result, code)

    def test_two_bracketed(self):
        code = '{_x=2;_y=3;};'
        result = parse(code)
        expected = Statement([Statement([Code([
            Statement([V('_x'), Keyword('='), N(2)], ending=';'),
            Statement([V('_y'), Keyword('='), N(3)], ending=';')])], ending=';')])

        self.assertEqualStatement(expected, result, code)

    def test_assign_with_parenthesis(self):
        code = "_x=(_y==2);"
        result = parse(code)

        s1 = Statement([V('_y'), Keyword('=='), N(2)])
        expected = Statement([Statement([V('_x'), Keyword('='), Statement([s1], parenthesis=True)], ending=';')])

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
            ])], ending=';')])

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
                                         Code([Statement([V('_x'), Keyword('=='), N(1)])])], ending=';')])
        
        self.assertEqualStatement(expected, result, code)

    def test_if_then_else(self):
        code = 'if(true)then{1}else{2}'
        result = parse(code)
        expected = \
            Statement([
                Statement([
                    Statement([
                        KeywordControl('if'),
                        Statement([
                            Statement([Boolean(True)])], parenthesis=True),
                    ]),
                    KeywordControl('then'),
                    Statement([
                        Code([Statement([N(1)])]),
                        KeywordControl('else'),
                        Code([Statement([N(2)])]),
                    ])
                ])
            ])
        self.assertEqualStatement(expected, result, code)

    def test_switch(self):
        code = 'switch (0) do {}'
        result = parse(code)
        expected = \
            Statement([
                Statement([
                    Statement([
                        KeywordControl('switch'),
                        Statement([Space(), Statement([Statement([N(0)])], parenthesis=True), Space()]),
                    ]),
                    KeywordControl('do'),
                    Statement([
                        Space(), Code([])
                    ])
                ])
            ])
        self.assertEqualStatement(expected, result, code)

    def test_position(self):
        code = '_x=2 _y=3;'
        result = parse(code)
        self.assertEqual(result[0][1].position, (1, 3))

    def test_define(self):
        code = "#define CHECK \\\n1"
        result = parse(code)
        expected = \
            Statement([
                Statement([
                    Statement([
                        Keyword('#define'), Space(), V('CHECK'), Space(), BrokenEndOfLine(), N(1)
            ])])])

        self.assertEqualStatement(expected, result, code)

    def test_include(self):
        code = '#include "macros.hpp"\n_x = 1'
        result = parse(code)
        expected = \
            Statement([
                Statement([
                    Statement([
                        Keyword('#include'), Space(), String('"macros.hpp"')
                ])]),
                Statement([
                    Statement([
                        EndOfLine('\n'), V("_x"), Space()]), Keyword('='), Statement([Space(), N(1)])
                ])
            ])

        self.assertEqualStatement(expected, result, code)

    def test_signed_precedence(self):
        code = "_x = -1"
        result = parse(code)
        expected = \
            Statement([
                Statement([
                    Statement([V('_x'), Space()]),
                    Keyword('='),
                    Statement([Space(), Keyword('-'), N(1)])
                ])
            ])
        self.assertEqualStatement(expected, result, code)

    def test_for(self):
        code = 'for "_i" from 0 to 10 do {}'
        expected = \
            Statement([
                Statement([
                    Statement([
                        Statement([
                            Statement([
                                KeywordControl('for'),
                                Statement([Space(), String('"_i"'), Space()])
                            ]),
                            KeywordControl('from'),
                            Statement([Space(), N(0), Space()]),
                        ]),
                        KeywordControl('to'),
                        Statement([Space(), N(10), Space()]),
                    ]),
                    KeywordControl('do'),
                    Statement([Space(), Code([])])
                ])
            ])
        self.assertEqualStatement(expected, parse(code), code)

    def test_while(self):
        code = 'while {} do {}'
        expected = \
            Statement([
                Statement([
                    Statement([
                        KeywordControl('while'),
                        Statement([
                            Space(), Code([]), Space()
                        ])
                    ]),
                    KeywordControl('do'),
                    Statement([
                        Space(), Code([])
                    ])
                ])
            ])
        self.assertEqualStatement(expected, parse(code), code)

    def test_parse_keyword_constant(self):
        code = '_x = west'
        expected = Statement([Statement([Statement([
            V('_x'), Space()]),
            Keyword('='), Statement([Space(), KeywordConstant('west'),
            ])])])
        self.assertEqualStatement(expected, parse(code), code)

    def test_private(self):
        code = 'private _x = 2'
        expected = \
            Statement([
                Statement([
                    Statement([
                        Keyword('private'), Statement([Space(), V('_x'), Space()])
                    ]),
                    Keyword('='), Statement([Space(), N(2)])
                ])
            ])
        self.assertEqualStatement(expected, parse(code), code)

    def test_params_simple(self):
        code = 'params ["_x"]'
        # S<S<K<params>' '[S<s<"_x">>]>>
        expected = \
            Statement([
                Statement([
                    Keyword('params'), Space(), Array([Statement([String('"_x"')])])
                ])
            ])
        self.assertEqualStatement(expected, parse(code), code)

    def test_params_call(self):
        code = '[1] params ["_x"]'
        expected = \
            Statement([
                Statement([
                    Array([Statement([N(1)])]), Space(),
                    Keyword('params'), Space(), Array([Statement([String('"_x"')])])
                ])
            ])
        self.assertEqualStatement(expected, parse(code), code)

    def test_try_catch(self):
        code = 'try {} catch {}'
        expected = \
            Statement([
                Statement([
                    Statement([
                        KeywordControl('try'),
                        Statement([Space(), Code([]), Space()]),
                    ]),
                    KeywordControl('catch'),
                    Statement([Space(), Code([])]),
                ])
            ])
        self.assertEqualStatement(expected, parse(code), code)

    def test_exa(self):
        code = '1,2'
        expected = \
            Statement([
                Statement([
                    N(1)], ending=','),
                Statement([N(2)])
            ])
        self.assertEqualStatement(expected, parse(code), code)


class ParseArray(ParserTestCase):

    def test_basic(self):
        test = '["AirS", nil];'
        result = parse(test)
        expected = Statement([Statement([
            Array([Statement([String('"AirS"')]), Statement([Space(), Keyword('nil')])])], ending=';')])

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
        expected = Statement([Statement([Array([Statement([])])], ending=';')])

        self.assertEqualStatement(expected, result, code)

    def test_parse_3(self):
        code = '[1, 2, 3]'
        result = parse(code)
        expected = Statement([Statement([
            Array([Statement([N(1)]), Statement([Space(), N(2)]), Statement([Space(), N(3)])])
        ])])

        self.assertEqual(expected, result, code)

    def test_or_together(self):
        code = '||isNull'
        result = parse(code)
        expected = Statement([Statement([
            Keyword('||'), Keyword('isNull')
        ])])
        self.assertEqualStatement(expected, result, code)


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
            Statement([Space(), N(2)])], ending=';'),
            Statement([Space(), Comment('// the two')])
        ])

        self.assertEqualStatement(expected, result, code)

    def test_inline_with_eol(self):
        code = '_x=2;// the two\n_x=3;'
        result = parse(code)
        expected = Statement([
            Statement([V('_x'), Keyword('='), N(2)], ending=';'),
            Statement([Statement([Comment('// the two\n'), V('_x')]), Keyword('='), N(3)], ending=';')])

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
            N(2)], ending=';'),
            Statement([Statement([Comment('/* the two \n the three\n the four\n */'),
                                  EndOfLine('\n'), V('_x')]), Keyword('='), N(3)])
        ])

        self.assertEqualStatement(expected, result, code)

    def test_with_other_comment(self):
        code = '_x=2;/* // two four\n */\n_x=3'
        result = parse(code)
        expected = Statement([Statement([
            V('_x'),
            Keyword('='),
            N(2)], ending=';'),
            Statement(
                [Statement([Comment('/* // two four\n */'), EndOfLine('\n'), V('_x')]), Keyword('='), N(3)])
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


class ParsePreprocessor(ParserTestCase):

    def test_define(self):
        code = "#define a(_x) \\\n(_x==2)"
        result = parse(code)
        expected = \
            Statement([
                Statement([
                    Statement([
                        Keyword('#define'), Space(), V('a'),
                        Statement([
                            Statement([V('_x')])
                        ], parenthesis=True),
                        Space(), BrokenEndOfLine(),
                        Statement([
                            Statement([V('_x'), Keyword('=='), N(2)])
                        ], parenthesis=True)
                    ])
                ])
            ])
        self.assertEqualStatement(expected, result, code)

    def test_define_with_comment(self):
        code = "a\n// 1.\n#define a\n"
        result = parse(code)
        self.assertEqual(str(result), code)
