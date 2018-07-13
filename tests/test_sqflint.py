import sys
import os
import io
from contextlib import contextmanager
from unittest import TestCase

from sqflint import parse_args, entry_point


@contextmanager
def captured_output():
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class ParseCode(TestCase):

    def test_stdin(self):
        with captured_output() as (out, err):
            sys.stdin = io.StringIO()
            sys.stdin.write('hint _x')
            sys.stdin.seek(0)
            entry_point([])

        self.assertEqual(
            out.getvalue(),
            '[1,5]:warning:Local variable "_x" is not from this scope (not private)\n')

    def test_parser_error(self):
        with captured_output() as (out, err):
            sys.stdin = io.StringIO()
            sys.stdin.write('hint (_x')
            sys.stdin.seek(0)
            entry_point([])

        self.assertEqual(
            out.getvalue(),
            '[1,5]:error:Parenthesis "(" not closed\n')

    def test_directory(self):
        args = parse_args(['--directory', 'tests/test_dir'])
        self.assertEqual('tests/test_dir', args.directory)

    def test_exit_code(self):
        with captured_output():
            exit_code = entry_point(['tests/test_dir/test.sqf'])
        self.assertEqual(exit_code, 0)

        # there are no errors, only a warning
        with captured_output():
            exit_code = entry_point(['tests/test_dir/test.sqf', '-e', 'e'])
        self.assertEqual(exit_code, 0)

        with captured_output():
            exit_code = entry_point(['tests/test_dir/test.sqf', '-e', 'w'])
        self.assertEqual(exit_code, 1)

    def test_filename_run(self):
        with captured_output() as (out, err):
            entry_point(['tests/test_dir/test.sqf'])

        self.assertEqual(out.getvalue(),
                         '[1,5]:warning:Local variable "_x" is not from this scope (not private)\n')

    def test_directory_run(self):
        with captured_output() as (out, err):
            entry_point(['--directory', 'tests/test_dir'])

        self.assertEqual(
            out.getvalue(),
            'test.sqf\n\t[1,5]:warning:Local variable "_x" is not from this scope (not private)\n'
            'test1.sqf\n\t[1,5]:warning:Local variable "_y" is not from this scope (not private)\n')

    def test_directory_run_to_file(self):
        entry_point(['--directory', 'tests/test_dir', '-o', 'tests/result.txt'])

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
