import math

from sqf.types import Number, Array, Code, Type, Boolean, String, Nothing, Variable
from sqf.keywords import Keyword, KeywordControl, Namespace
from sqf.interpreter_types import WhileType, ForType, ForFromType, ForFromToStepType, ForSpecType, SwitchType
from sqf.exceptions import ExecutionError, SQFSyntaxError


class Expression:
    """
    A generic class to represent an expression: it has a lenght, an action, and tests
    to identify it.
    """
    def __init__(self, length, action=None, tests=None):
        self.length = length
        if tests is None:
            tests = []
        self.tests = tests
        if action is None:
            action = lambda t, v, i: True
        self.action = action

    def is_match(self, values):
        if len(values) != self.length:
            return False

        for test in self.tests:
            if not test(values):
                return False
        else:
            return True

    def execute(self, tokens, values, interpreter):
        return self.action(tokens, values, interpreter)


class UnaryExpression(Expression):
    def __init__(self, op_name, rhs_type, action, tests=None):
        self._op_name = op_name

        if tests is None:
            tests = []
        super().__init__(2, action, [
            lambda values: values[0] == Keyword(op_name),
            lambda values: isinstance(values[1], rhs_type),
            ] + tests)

    def execute(self, tokens, values, interpreter):
        return self.action(values[1], interpreter)


class BinaryExpression(Expression):
    def __init__(self, op_name, lhs_type, rhs_type, action=None, tests=None):
        self._op_name = op_name
        if tests is None:
            tests = []
        if action is None:
            action = lambda lhs_v, rhs_v, i: True
        super().__init__(3, action, [
            lambda values: values[1] == Keyword(op_name),
            lambda values: isinstance(values[0], lhs_type),
            lambda values: isinstance(values[2], rhs_type),
            ] + tests)

    def execute(self, tokens, values, interpreter):
        lhs_v = values[0]
        rhs_v = values[2]
        return self.action(lhs_v, rhs_v, interpreter)


class ComparisonExpression(BinaryExpression):

    def __init__(self, op_name):
        assert(Keyword(op_name) in OP_COMPARISON)
        tests = [lambda values: type(values[0]) == type(values[2]),
                 lambda values: not (type(values[0]) == Boolean == type(values[2]))]
        super().__init__(op_name, Type, Type, tests=tests)

    def execute(self, tokens, values, _):
        lhs_v = values[0]
        op = values[1]
        rhs_v = values[2]
        return Boolean(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))


class ArithmeticExpression(BinaryExpression):

    def __init__(self, op_name):
        op = Keyword(op_name)
        assert (op in OP_ARITHMETIC)
        tests = [lambda values: type(values[0]) == type(values[2]) == Array and
                                op in OP_ARRAY_OPERATIONS or
                                type(values[0]) == type(values[2]) == String and
                                op == Keyword('+') or
                                type(values[0]) == type(values[2]) == Number]
        super().__init__(op.value, Type, Type, tests=tests)

    def execute(self, tokens, values, _):
        lhs_v = values[0]
        op = values[1]
        rhs_v = values[2]
        lhs_t = type(values[0])
        if type(lhs_v) == Array:
            return Array(OP_ARRAY_OPERATIONS[op](lhs_v.value, rhs_v.value))
        if type(lhs_v) == String:
            container = lhs_v.container
            return String(container + OP_ARRAY_OPERATIONS[op](lhs_v.value, rhs_v.value) + container)
        else:
            return lhs_t(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))


class LogicalExpression(BinaryExpression):
    def __init__(self, op_name):
        assert (Keyword(op_name) in OP_LOGICAL)

        tests = [lambda values: type(values[0]) == type(values[2]) == Boolean]
        super().__init__(op_name, Type, Type, tests=tests)

    def execute(self, tokens, values, _):
        lhs_v = values[0]
        op = values[1]
        rhs_v = values[2]
        return Boolean(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))


class IfThenExpression(Expression):

    def __init__(self, length, tests, action):
        base_test = lambda values: values[0] == KeywordControl('if') and \
                                   isinstance(values[1], Boolean) and values[2] == KeywordControl('then')

        super().__init__(length, action, [base_test] + tests)

    def execute(self, tokens, values, interpreter):
        return self.action(values, interpreter)


def _while_loop(interpreter, condition_code, do_code):
    outcome = Nothing
    while True:
        condition_outcome = interpreter.execute_code(condition_code)
        if condition_outcome.value is False:
            break
        outcome = interpreter.execute_code(do_code)
    return outcome


class WhileExpression(Expression):
    """
    Catches `While {}` expression and stores it as a WhileType
    """
    def __init__(self):
        super().__init__(2, lambda t, v, i: WhileType(v[1]), [
            lambda values: values[0] == KeywordControl('while') and isinstance(values[1], Code)
        ])


class WhileDoExpression(Expression):
    def __init__(self):
        super().__init__(3, lambda t, v, i: _while_loop(i, v[0].condition, v[2]), [
            lambda values: type(values[0]) == WhileType and
                           values[1] == KeywordControl('do') and
                           type(values[2]) == Code
        ])


class ForSpecExpression(Expression):
    def __init__(self):
        super().__init__(2, lambda t, v, i: ForSpecType(v[1]), [
            lambda values: values[0] == KeywordControl('for') and isinstance(values[1], Array) and
            len(values[1]) == 3
        ])


def _forspecs_loop(interpreter, start_code, stop_code, increment_code, do_code):
    outcome = Nothing

    interpreter.execute_code(start_code)
    while True:
        condition_outcome = interpreter.execute_code(stop_code)
        if condition_outcome.value is False:
            break

        outcome = interpreter.execute_code(do_code)
        interpreter.execute_code(increment_code)
    return outcome


class ForSpecDoExpression(Expression):
    def __init__(self):
        super().__init__(3, lambda t, v, i: _forspecs_loop(i, v[0].array[0], v[0].array[1], v[0].array[2], v[2]), [
            lambda values: type(values[0]) == ForSpecType and
                           values[1] == KeywordControl('do') and
                           type(values[2]) == Code
        ])


class ForExpression(Expression):
    def __init__(self):
        super().__init__(2, lambda t, v, i: ForType(v[1]), [
            lambda values: values[0] == KeywordControl('for') and isinstance(values[1], String)
        ])


class ForFromExpression(Expression):
    def __init__(self):
        super().__init__(3, lambda t, v, i: ForFromType(v[0].variable, v[2]), [
            lambda values: type(values[0]) == ForType and
                           values[1] == KeywordControl('from') and
                           type(values[2]) == Number
        ])


class ForFromToExpression(Expression):
    def __init__(self):
        super().__init__(3, lambda t, v, i: ForFromToStepType(v[0].variable, v[0].from_, v[2]), [
            lambda values: type(values[0]) == ForFromType and
                           values[1] == KeywordControl('to') and
                           type(values[2]) == Number
        ])


class ForFromToStepExpression(Expression):
    def __init__(self):
        super().__init__(3, lambda t, v, i: ForFromToStepType(v[0].variable, v[0].from_, v[0].to, v[2]), [
            lambda values: type(values[0]) == ForFromToStepType and
                           values[1] == KeywordControl('step') and
                           type(values[2]) == Number
        ])


def _forvar_loop(interpreter, token_name, start, stop, step, code):
    outcome = Nothing
    for i in range(start, stop + 1, step):
        outcome = interpreter.execute_code(code, extra_scope={token_name: Number(i)})
    return outcome


class ForFromToDoExpression(Expression):
    def __init__(self):
        super().__init__(3, lambda t, v, i: _forvar_loop(i, v[0].variable.value, v[0].from_.value, v[0].to.value, v[0].step.value, v[2]), [
            lambda values: type(values[0]) == ForFromToStepType and
                           values[1] == KeywordControl('do') and
                           type(values[2]) == Code
        ])


class SwitchExpression(Expression):
    def __init__(self):
        super().__init__(2, lambda t, v, i: SwitchType(v[1]), [
            lambda values: values[0] == KeywordControl('switch') and
                           isinstance(values[1], Type)
        ])


def _switch(interpreter, result, code):
    default = None
    outcome = None

    # a flag that is set to True when a case is fulfilled and the next outcome_statement is to be run.
    run_next = False

    for statement in code.base_tokens:
        if not statement.base_tokens:
            pass
        elif statement.base_tokens[0] == KeywordControl('default'):
            if default is not None:
                raise SQFSyntaxError(code.position, 'Switch code contains more than 1 `default`')
            default = statement.base_tokens[1]
        elif statement.base_tokens[0] == KeywordControl('case') and (
                    len(statement.base_tokens) == 2 or
                    len(statement.base_tokens) == 4 and statement.base_tokens[2] == Keyword(':')):
            condition_statement = statement.base_tokens[1]
            if len(statement.base_tokens) == 2:
                outcome_statement = None
            else:
                outcome_statement = statement.base_tokens[3]

            condition_outcome = interpreter.execute_token(condition_statement)[1]

            if outcome_statement and run_next:
                outcome = interpreter.execute_code(outcome_statement)
                break
            elif condition_outcome == result:
                if outcome_statement:
                    outcome = interpreter.execute_code(outcome_statement)
                    break
                else:
                    run_next = True
        else:
            raise SQFSyntaxError(statement.position, 'Switch statement "%s" is syntactically wrong' % statement)

    if outcome is None:
        if default is not None:
            outcome = interpreter.execute_code(default)
        else:
            outcome = Boolean(True)

    return outcome


class SwitchDoExpression(Expression):
    def __init__(self):
        super().__init__(3, lambda t, v, i: _switch(i, v[0].result, v[2]), [
            lambda values: type(values[0]) == SwitchType and
                           values[1] == KeywordControl('do') and
                           isinstance(values[2], Code)
        ])


def _select_array(lhs_v, rhs_v, _):
    start = rhs_v.value[0].value
    count = rhs_v.value[1].value
    return Array(lhs_v.value[start:start + count])


def _find(lhs_v, rhs_v, _):
    try:
        index = next(i for i, v in enumerate(lhs_v.value) if v == rhs_v)
    except StopIteration:
        index = -1
    return Number(index)


def _pushBack(lhs_v, rhs_v, _):
    lhs_v.append(rhs_v)
    return Number(len(lhs_v.value) - 1)


def _pushBackUnique(lhs_v, rhs_v, _):
    if rhs_v in lhs_v.value:
        return Number(-1)
    else:
        lhs_v.append(rhs_v)
        return Number(len(lhs_v.value) - 1)


def _setVariable(lhs_v, rhs_v, interpreter):
    namespace_name = lhs_v.value

    # get the variable name
    variable_name = rhs_v.value[0].value
    # get the value
    rhs_assignment = interpreter.execute_token(rhs_v.value[1])[1]

    variable_scope = interpreter.get_scope(variable_name, namespace_name)
    variable_scope[variable_name] = rhs_assignment
    return Nothing


def _getVariableString(lhs_v, rhs_v, interpreter):
    return interpreter.value(Variable(rhs_v.value), lhs_v.value)


def _getVariableArray(lhs_v, rhs_v, interpreter):
    outcome = interpreter.value(Variable(rhs_v.value[0].value), lhs_v.value)
    if outcome == Nothing:
        outcome = rhs_v.value[1]
    return outcome


def _addPublicVariableEventHandler(lhs_v, rhs_v, interpreter):
    if interpreter.simulation:
        interpreter.client.add_listening(lhs_v.value, rhs_v)
    else:
        raise ExecutionError('"addPublicVariableEventHandler" called without a client')


def _if_then_else(interpreter, condition, then, else_=None):
    if condition.value is True:
        return interpreter.execute_code(then)
    else:
        if else_:
            return interpreter.execute_code(else_)
        else:
            return Nothing


EXPRESSIONS = [
    WhileExpression(),
    WhileDoExpression(),

    ForExpression(),
    ForFromExpression(),
    ForFromToExpression(),
    ForFromToStepExpression(),
    ForFromToDoExpression(),
    ForSpecExpression(),
    ForSpecDoExpression(),
    SwitchExpression(),
    SwitchDoExpression(),

    # Unary
    UnaryExpression('-', Number, lambda rhs_v, i: Number(-rhs_v.value)),
    UnaryExpression('floor', Number, lambda rhs_v, i: Number(math.floor(rhs_v.value))),
    UnaryExpression('reverse', Array, lambda rhs_v, i: rhs_v.reverse()),
    UnaryExpression('createMarker', Array, lambda rhs_v, i: i.create_marker(rhs_v)),
    # Binary
    BinaryExpression('set', Array, Array, lambda lhs_v, rhs_v, i: lhs_v.set(rhs_v)),

    # Array related
    BinaryExpression('resize', Array, Number, lambda lhs_v, rhs_v, i: lhs_v.resize(rhs_v.value)),
    UnaryExpression('count', Array, lambda rhs_v, i: Number(len(rhs_v.value))),
    BinaryExpression('in', Type, Array, lambda lhs_v, rhs_v, i: Boolean(lhs_v in rhs_v.value)),

    BinaryExpression('select', Array, (Number, Boolean), lambda lhs_v, rhs_v, i: lhs_v.value[int(round(rhs_v.value))]),
    BinaryExpression('select', Array, Array, _select_array),

    BinaryExpression('find', Array, Type, _find),
    BinaryExpression('find', String, String, lambda lhs_v, rhs_v, i: Number(lhs_v.value.find(rhs_v.value))),

    BinaryExpression('pushBack', Array, Type, _pushBack),
    BinaryExpression('pushBackUnique', Array, Type, _pushBackUnique),
    BinaryExpression('append', Array, Array, lambda lhs_v, rhs_v, i: lhs_v.add(rhs_v.value)),

    UnaryExpression('toArray', String, lambda rhs_v, i: Array([Number(ord(s)) for s in rhs_v.value])),
    UnaryExpression('toString', Array, lambda rhs_v, i: String('"'+''.join(chr(s.value) for s in rhs_v.value)+'"')),

    # code and namespaces
    UnaryExpression('call', Code, lambda rhs_v, i: i.execute_code(rhs_v)),
    BinaryExpression('call', Array, Code, lambda lhs_v, rhs_v, i: i.execute_code(rhs_v, params=lhs_v)),

    BinaryExpression('setVariable', Namespace, Array, _setVariable, tests=[lambda values: len(values[2].value) == 2]),

    BinaryExpression('getVariable', Namespace, String, _getVariableString),
    BinaryExpression('getVariable', Namespace, Array, _getVariableArray,
                     tests=[lambda values: len(values[2].value) == 2]),

    BinaryExpression('addPublicVariableEventHandler', String, Code, _addPublicVariableEventHandler),

    IfThenExpression(4, tests=[lambda values: type(values[3]) == Code],
                     action=lambda v, i: _if_then_else(i, v[1], v[3])),
    IfThenExpression(4, tests=[lambda values: type(values[3]) == Array],
                     action=lambda v, i: _if_then_else(i, v[1], v[3].value[0], v[3].value[1])),
    IfThenExpression(6, tests=[lambda values: type(values[3]) == Code,
                               lambda values: values[4] == KeywordControl('else'),
                               lambda values: type(values[5]) == Code],
                     action=lambda v, i: _if_then_else(i, v[1], v[3], v[5])),
]


OP_ARITHMETIC = [Keyword(s) for s in ('+', '-', '*', '/', '%', 'mod', '^', 'max', 'floor')]

OP_LOGICAL = [Keyword(s) for s in ('&&', 'and', '||', 'or')]

OP_COMPARISON = [Keyword(s) for s in ('==', '!=', '<', '>', '<=', '>=')]

OP_OPERATIONS = {
    Keyword('+'): lambda x, y: x + y,
    Keyword('-'): lambda x, y: x - y,
    Keyword('*'): lambda x, y: x * y,
    Keyword('/'): lambda x, y: x / y,
    Keyword('%'): lambda x, y: x % y,
    Keyword('mod'): lambda x, y: x % y,
    Keyword('^'): lambda x, y: x ** y,

    Keyword('=='): lambda x, y: x == y,
    Keyword('!='): lambda x, y: x != y,
    Keyword('<'): lambda x, y: x < y,
    Keyword('>'): lambda x, y: x < y,
    Keyword('<='): lambda x, y: x <= y,
    Keyword('>='): lambda x, y: x >= y,

    Keyword('&&'): lambda x, y: x and y,
    Keyword('and'): lambda x, y: x and y,
    Keyword('||'): lambda x, y: x or y,
    Keyword('or'): lambda x, y: x or y,

    Keyword('max'): lambda x, y: max(x, y),
    Keyword('floor'): lambda x: math.floor(x),
}


def _subtract_lists(x, y):
    yset = set([y_i.value for y_i in y])
    return [x_i for x_i in x if x_i.value not in yset]


OP_ARRAY_OPERATIONS = {
    Keyword('+'): lambda x, y: x + y,
    Keyword('-'): lambda x, y: _subtract_lists(x, y),
}


for operator in OP_COMPARISON:
    EXPRESSIONS.append(ComparisonExpression(operator.value))
for operator in OP_ARITHMETIC:
    EXPRESSIONS.append(ArithmeticExpression(operator.value))
for operator in OP_LOGICAL:
    EXPRESSIONS.append(LogicalExpression(operator.value))
