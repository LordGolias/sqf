import sys
import os
import io
from unittest import TestCase

from sqflint import parse_args, main


class ParseCode(TestCase):

    def setUp(self):
        self.stdout = io.StringIO()
        sys.stdout = self.stdout

    def tearDown(self):
        sys.stdout = sys.__stdout__
        sys.stdin = sys.__stdin__

    def test_stdin(self):
        sys.stdin = io.StringIO()
        sys.stdin.write('hint _x')
        sys.stdin.seek(0)
        main([])
        self.assertEqual(
            self.stdout.getvalue(),
            '[1,5]:warning:Local variable "_x" is not from this scope (not private)\n')

    def test_directory(self):
        args = parse_args(['--directory', 'tests/test_dir'])
        self.assertEqual('tests/test_dir', args.directory)

    def test_exit_code(self):
        exit_code = main(['tests/test_dir/test.sqf'])
        self.assertEqual(exit_code, 0)

        # there are no errors, only a warning
        exit_code = main(['tests/test_dir/test.sqf', '-e', 'e'])
        self.assertEqual(exit_code, 0)

        exit_code = main(['tests/test_dir/test.sqf', '-e', 'w'])
        self.assertEqual(exit_code, 1)

    def test_filename_run(self):
        main(['tests/test_dir/test.sqf'])
        self.assertEqual(self.stdout.getvalue(),
                         '[1,5]:warning:Local variable "_x" is not from this scope (not private)\n')

    def test_directory_run(self):
        main(['--directory', 'tests/test_dir'])
        result = self.stdout.getvalue()
        self.assertEqual(
            result,
            'test.sqf\n\t[1,5]:warning:Local variable "_x" is not from this scope (not private)\n'
            'test1.sqf\n\t[1,5]:warning:Local variable "_y" is not from this scope (not private)\n')

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
