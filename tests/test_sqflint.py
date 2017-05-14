import sys
import os
import io
from unittest import TestCase, expectedFailure

from sqflint import parse_args, main


class ParseCode(TestCase):

    def setUp(self):
        self.old_stdout = sys.stdout

        self.stdout = io.StringIO()
        sys.stdout = self.stdout

    def tearDown(self):
        sys.stdout = self.old_stdout

    # def test_stdin(self):
    #     result = main([])
    #     self.assertEqual(None, result)

    def test_directory(self):
        args = parse_args(['--directory', 'tests/test_dir'])
        self.assertEqual('tests/test_dir', args.directory)

    # @expectedFailure
    # def test_filename_run(self):
    #     result = main(['tests/test_dir/test.sqf'])
    #     self.assertEqual(result,
    #                      '[1,5]:warning:Local variable "_x" is not from this scope (not private)\n')

    # def test_directory_run(self):
    #     result = main(['--directory', 'tests/test_dir'])
    #     self.assertEqual(
    #         result,
    #         'test.sqf\n\t[1,5]:warning:Local variable "_x" is not from this scope (not private)\n'
    #         'test1.sqf\n\t[1,5]:warning:Local variable "_y" is not from this scope (not private)\n')

    def test_directory_run_to_file(self):
        main(['--directory', 'tests/test_dir', '-o', 'tests/result.txt'])

        with open('tests/result.txt') as f:
            result = f.read()

        try:
            os.remove('tests/result.txt')
        except OSError:
            pass

        self.assertEqual(
            result,
            'test.sqf\n\t[1,5]:warning:Local variable "_x" is not from this scope (not private)\n'
            'test1.sqf\n\t[1,5]:warning:Local variable "_y" is not from this scope (not private)\n')
