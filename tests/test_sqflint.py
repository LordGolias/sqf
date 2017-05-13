import sys
import os
import io
from unittest import TestCase

from sqflint import parse_args, main


class ParseCode(TestCase):

    def setUp(self):
        self.old_stdout = sys.stdout

        self.stdout = io.StringIO()
        sys.stdout = self.stdout

    def tearDown(self):
        sys.stdout = self.old_stdout

    def test_filename(self):
        args = parse_args(['test_dir/test.sqf'])
        self.assertEqual('r', args.file.mode)

    def test_directory(self):
        args = parse_args(['--directory', 'test_dir'])
        self.assertEqual('test_dir', args.directory)

    def test_filename_run(self):
        main(['test_dir/test.sqf'])
        self.assertEqual(self.stdout.getvalue(),
                         '[1,5]:warning:Local variable "_x" is not from this scope (not private)\n')

    def test_directory_run(self):
        main(['--directory', 'test_dir'])
        self.assertEqual(
            self.stdout.getvalue(),
            'test.sqf\n\t[1,5]:warning:Local variable "_x" is not from this scope (not private)\n'
            'test1.sqf\n\t[1,5]:warning:Local variable "_y" is not from this scope (not private)\n')

    def test_directory_run_to_file(self):
        main(['--directory', 'test_dir', '-o', 'result.txt'])

        with open('result.txt') as f:
            result = f.read()

        try:
            os.remove('result.txt')
        except OSError:
            pass

        self.assertEqual(
            result,
            'test.sqf\n\t[1,5]:warning:Local variable "_x" is not from this scope (not private)\n'
            'test1.sqf\n\t[1,5]:warning:Local variable "_y" is not from this scope (not private)\n')
