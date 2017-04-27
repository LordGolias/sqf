from unittest import TestCase
from sqf.types import Statement, Code, Array, String, Variable as V, \
    Number as N
from sqf.keywords import Keyword
from sqf.parser_types import Space

from sqf.cofigFile.parser import parse
from sqf.cofigFile.interpreter import interpret


class Parser(TestCase):

    def test_assigment(self):
        x = parse('version = 52;')
        self.assertEqual(Statement([V('version'), Space(), Keyword('='), Space(), N(52), Keyword(';')]), x[0])

    def test_class(self):
        code = '''class EditorData {moveGridStep = 1.0;}'''
        x = parse(code)
        expected = Statement([Statement([
            Keyword('class'), Space(), V('EditorData'), Space(),
            Code([Statement([V('moveGridStep'), Space(), Keyword('='), Space(), N(1.0), Keyword(';')])])])])

        self.assertEqual(expected, x)

    def test_array(self):
        code = 'pos[] = {10253.095,59.11644,13849.58};'
        result = parse(code)
        expected = Statement([Statement([
            V('pos'), Array([Statement([])]), Space(), Keyword('='), Space(),
            Code([Statement([N(10253.095), Keyword(','), N(59.11644), Keyword(','), N(13849.58)])]), Keyword(';')])])

        self.assertEqual(expected, result)


class Interpreter(TestCase):

    def test_assigment(self):
        interpreter = interpret('version = 52;')

        self.assertEqual({'version': N(52)}, interpreter)

    def test_class(self):
        code = '''class EditorData {moveGridStep = 1.0;}'''
        interpreter = interpret(code)

        self.assertEqual({'EditorData': {'moveGridStep': N(1.0)}}, interpreter)

    def test_array(self):
        code = 'pos[] = {10253.095,59.11644,13849.58};'
        interpreter = interpret(code)
        self.assertEqual({'pos': Array([N(10253.095), N(59.11644), N(13849.58)])}, interpreter)

    def test_define(self):
        code = '''
        #define _ARMA_

//Class WholeLottaAltis.Altis : mission.sqm{
version = 52;
'''
        result = interpret(code)
        self.assertEqual({'version': N(52)}, result)

    def test_random(self):
        code = '''
    version = 52;
    class EditorData
    {
    	moveGridStep = 1.0;
    	class ItemIDProvider
    	{
    		nextID = 817;
    	};
    	class MarkerIDProvider
    	{
    		nextID = 124;
    	};
    	class Camera
    	{
    		pos[] = {10253.095,59.11644,13849.58};
    	};
    };
    addons[] = {"A3_Structures_F_Mil_Helipads","A3_Soft_F_Truck","A3_Soft_F_MRAP_03"};
    '''
        interpreter = interpret(code)
        expected = {
            'version': N(52),
            'EditorData': {
                'moveGridStep': N(1.0),
                'ItemIDProvider': {'nextID': N(817)},
                'MarkerIDProvider': {'nextID': N(124)},
                'Camera': {'pos': Array([N(10253.095), N(59.11644), N(13849.58)])},
            },
            'addons': Array([String('"A3_Structures_F_Mil_Helipads"'),
                             String('"A3_Soft_F_Truck"'),
                             String('"A3_Soft_F_MRAP_03"')])
        }

        self.assertEqual(expected, interpreter)
