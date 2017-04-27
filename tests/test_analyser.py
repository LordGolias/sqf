from unittest import TestCase

from sqf.parser import parse
from sqf.analyser import analyze


class AnalyseTestCase(TestCase):

    def test_statement(self):
        code = '_x=2 _y=3;'
        result = parse(code)

        errors = analyze(result)

        self.assertEqual(len(errors), 1)
        self.assertEqual((1, 6), errors[0].position)

    def test_code(self):
        code = """x = {
    call {_x=1 _y = 2;}
}"""
        errors = analyze(parse(code))
        self.assertEqual(len(errors), 1)
        self.assertEqual((2, 16), errors[0].position)
