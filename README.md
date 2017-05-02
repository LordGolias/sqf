[![Build Status](https://travis-ci.org/LordGolias/sqf.svg?branch=master)](https://travis-ci.org/LordGolias/sqf)
[![Coverage Status](https://coveralls.io/repos/github/LordGolias/sqf/badge.svg)](https://coveralls.io/github/LordGolias/sqf)

# SQF linter

This project contains a parser, compiler, static analyser and interpreter for 
SQF (Arma scripting language), written in Python.
It can be used to:

* syntax-check SQF
* static analyze SQF
* execute SQF on a virtual environment

## Problem it solves

One of the major bottlenecks in scripting in SQF is the time spent 
testing it in-game, by running the game.

Often, these scripts contain simple errors (missing ";") that everyone would 
love to avoid restarting the mission because of them.

This package allows to parse SQF in Python to check for syntactic errors,
wrong types, problems in variables scopes, etc.

The interpreter is able to run scripts on an emulated (and limited) environment of the simulation.
The interpreter is obviously *not intended* to run Arma simulation; it is
aimed for you, moder, run tests of your scripts (e.g. Unit Tests) 
without having to run the game.

### Parser example

    >>> code = '[1, 2, 3]'
    >>> sqf.parser.parse(code)
    Statement([Statement([
        Array([Statement([N(1)]), Statement([Space(), N(2)]), Statement([Space(), N(3)])])
    ])])

### Analyzer examples

    >>> code = 'if (true) {1}'
    >>> errors = sqf.analyzer.analyze(sqf.parser.parse(code))
    >>> errors[0]
    SQFParserError((1, 11), "'(true)' can't preceed '{1}' (missing ';'?)")

    >>> code = 'private _y = _z'
    >>> analyser = sqf.scope_analyzer.interpret(sqf.parser.parse(code))
    >>> analyser.exceptions[0]
    SQFWarning((1, 14), 'Local variable "_z" is not from this scope (not private)')

### Interpreter example

    from sqf.interpreter import interpret
    interpreter, outcome = interpret('_x = [1, 2]; _y = _x; reverse _y;')
    # outcome equals to "Nothing"
    # interpreter['_y'] equals to Array([Number(2), Number(1)])
    # interpreter['_x'] equals to Array([Number(2), Number(1)])  # <= _y is a reference

## Requirements and installation

This code is written in Python 3 and has no dependencies.
You can install it by going to its directory and running:

    pip install .

## Tests and coverage

The code is heavily tested (coverage 98%+), and the tests
can be found in `tests.py`. Run them using standard Python unittest.

## Compatibility with editors

* [atom-linter](https://atomlinter.github.io/): [linter-sqf](https://github.com/LordGolias/linter-sqf)
* [sublimeLinter](http://www.sublimelinter.com/en/latest/): [SublimeLinter-contrib-sqflint](https://github.com/LordGolias/SublimeLinter-contrib-sqflint)

The script `sqflint.py` is the public interface for linting.

## Features

### Implemented

* Types: Number, String, Array, etc.
* Comparison, arithmetic and logical operators
* expressions and parenthesis
* Control structures (e.g. `if`, `while`)
* Variables, Assignment, Code blocks, Scopes and private
* `_this` and `call`
* Namespaces
* Client and server interaction (e.g. `publicVariable`)
* Comments
* Parse `configFile`.

### Not implementable

* Positions
* Most functions that affect objects, groups and positions (e.g. `create*`)
* time simulation (e.g. `sleep`)

## Code organization

This code contains essentially 4 components, a **tokenizer**, 
a **parser**, **analyzer** and **interpreter**:

### Interpreter

The interpreter is a class that executes parsed scripts. It receives a 
`Statement` and executes it as per described in the [Arma 3' wiki](https://community.bistudio.com/wiki).
To automatically initialise the interpreter and execute code, run `interpret`: 
 
    >>> from sqf.interpreter import interpret
    >>> script = '''
    a = 0;
    b = true;
    for [{_i = 0}, {_i < 10 && b}, {_i = _i + 1}] do {
        a = a + 1;
        if (a >= 7) then {b = false}
    }
    '''
    >>> interpreter, outcome = interpret(script)
    >>> interpreter['a']
    Number(7)
    >>> outcome
    Boolean(False)

The call `interpreter['a']` returns the outermost `Scope`
of the `Namespace` `"missionNamespace"`, but you can use `setVariable`
and `getVariable` to interact with other namespaces.
`sqf.tests.test_interpreter` contains the tests of the implemented functionality.

The source is in `sqf/interpreter.py`, the tests in `tests/test_interpreter.py`.
The main loop of the interpreter is defined in `sqf/interpreter.py`, and the 
expressions it evaluates are defined in `sqf/expressions.py`.

### Analyzer

The analyzer consumes the result of the parser and checks for static errors.
The source is in `sqf/analyzer.py`, the tests in `tests/test_analyzer.py`.

### Parser

The parser transforms a string into a nested `Statement`, i.e. 
a nested list of instances of `types`, operators, and keywords defined in SQF.
For example,

    >>> from sqf.parser import parser
    >>> script = '_x=2;'
    >>> result = parse(script)
    >>> result
    Statement([Statement([Variable('_x'), Keyword('='), Number(2)], ending=';')])
    >>> script == str(result) # True

This rather convolved `result` takes into account operator precedence and
the meaning of the different parenthesis (`[]`, `{}`, `()`).
To transform the script into tokens used in the parser, the tokenizer is called.
`sqf.tests.test_parser` contains the tests.

### Tokenizer

The tokenizer transforms a string into a list of tokens split by the 
relevant tokens of SQF. E.g.

    >>> from sqf.base_tokenizer import tokenize
    >>> tokenize('/*_x = 1;*/')
    ['/*', '_x', ' ', '=', ' ', '1', ';', '*/']

The source can be found in `sqf.base_tokenizer`.

### Others

* keywords: `sqf.keywords`
* types: `sqf.types`
* interpreted expressions: `sqf.expressions`
* namespaces: `sqf.namespaces`
* Client and Server: `sqf.client`

## Licence

This code is licenced under BSD.

## Author

This code was written by Lord Golias, lord.golias1@gmail.com
