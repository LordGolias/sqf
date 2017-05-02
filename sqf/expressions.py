import math

from sqf.types import Number, Array, Code, Type, Boolean, String, Nothing, Variable
from sqf.keywords import Keyword, KeywordControl, Namespace
from sqf.interpreter_types import WhileType, \
    ForType, ForFromType, ForFromToStepType, ForSpecType, SwitchType, IfType, ElseType
from sqf.exceptions import ExecutionError, SQFSyntaxError


class Expression:
    """
    A generic class to represent an expression. The expression matches according to the
    types of their elements, listed in `types`.
    """
    def __init__(self, types_or_values):
        self.types_or_values = types_or_values

    def is_match(self, values):
        if len(values) != len(self.types_or_values):
            return False

        for ts_or_vs, value in zip(self.types_or_values, values):
            if not isinstance(ts_or_vs, (list, tuple)):
                ts_or_vs = (ts_or_vs,)
            passes = False
            for t_or_v in ts_or_vs:
                if isinstance(t_or_v, type):
                    if isinstance(value, t_or_v):
                        passes = True
                        break  # if any type matches, it passes
                else:  # is a value
                    if value == t_or_v:
                        passes = True
                        break
            if not passes:
                return False
        return True

    def execute(self, values, interpreter):
        raise NotImplementedError


class InterpreterExpression:
    """
    This is an expression whose evaluation is just the return of an InterpreterType.
    These can be evaluated safely without the risk of changing the state.
    """
    pass


class UnaryExpression(Expression):
    def __init__(self, op, rhs_type, action, tests=None):
        assert (isinstance(op, Keyword))
        if tests is None:
            tests = []
        self.action = action
        self.tests = tests
        super().__init__([op, rhs_type])

    def is_match(self, values):
        if super().is_match(values):
            for test in self.tests:
                if not test(values):
                    return False
            return True
        else:
            return False

    def execute(self, values, interpreter):
        return self.action(values[1], interpreter)


class BinaryExpression(Expression):
    def __init__(self, lhs_type, op, rhs_type, action=None, tests=None):
        assert(isinstance(op, Keyword))
        if tests is None:
            tests = []
        if action is None:
            action = lambda lhs_v, rhs_v, i: True

        self.action = action
        self.tests = tests
        super().__init__([lhs_type, op, rhs_type])

    def is_match(self, values):
        if super().is_match(values):
            for test in self.tests:
                if not test(values):
                    return False
            return True
        else:
            return False

    def execute(self, values, interpreter):
        return self.action(values[0], values[2], interpreter)


class ComparisonExpression(BinaryExpression):

    def __init__(self, op):
        assert(op in OP_COMPARISON)
        tests = [lambda values: type(values[0]) == type(values[2]),
                 lambda values: not (type(values[0]) == Boolean == type(values[2]))]
        super().__init__(Type, op, Type, tests=tests)

    def execute(self, values, _):
        lhs_v = values[0]
        op = values[1]
        rhs_v = values[2]
        return Boolean(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))


class ArithmeticExpression(BinaryExpression):

    def __init__(self, op):
        assert (op in OP_ARITHMETIC)
        tests = [lambda values: type(values[0]) == type(values[2]) == Array and
                                op in OP_ARRAY_OPERATIONS or
                                type(values[0]) == type(values[2]) == String and
                                op == Keyword('+') or
                                type(values[0]) == type(values[2]) == Number]
        super().__init__(Type, op, Type, tests=tests)

    def execute(self, values, _):
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
    def __init__(self, op):
        assert (op in OP_LOGICAL)
        self._op = op

        tests = [lambda values: type(values[0]) == type(values[2]) == Boolean]
        super().__init__(Type, op, Type, tests=tests)

    def execute(self, values, _):
        lhs_v = values[0]
        op = values[1]
        rhs_v = values[2]
        return Boolean(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))


def _while_loop(interpreter, condition_code, do_code):
    outcome = Nothing
    while True:
        condition_outcome = interpreter.execute_code(condition_code)
        if condition_outcome.value is False:
            break
        outcome = interpreter.execute_code(do_code)
    return outcome


class WhileExpression(UnaryExpression, InterpreterExpression):
    """
    Catches `While {}` expression and stores it as a WhileType
    """
    def __init__(self):
        super().__init__(KeywordControl('while'), Code,
                         lambda v, i: WhileType(v))


class WhileDoExpression(BinaryExpression):
    def __init__(self):
        super().__init__(WhileType, KeywordControl('do'), Code,
                         lambda lhs, rhs, i: _while_loop(i, lhs.condition, rhs))


class ForSpecExpression(UnaryExpression, InterpreterExpression):
    def __init__(self):
        super().__init__(KeywordControl('for'), Array,
                         lambda v, i: ForSpecType(v), [lambda values: len(values[1]) == 3])


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


class ForSpecDoExpression(BinaryExpression):
    def __init__(self):
        super().__init__(ForSpecType, KeywordControl('do'), Code,
                         lambda lhs, rhs, i: _forspecs_loop(i, lhs.array[0], lhs.array[1], lhs.array[2], rhs))


class ForExpression(UnaryExpression, InterpreterExpression):
    def __init__(self):
        super().__init__(KeywordControl('for'), String, lambda rhs, i: ForType(rhs))


class ForFromExpression(BinaryExpression, InterpreterExpression):
    def __init__(self):
        super().__init__(ForType, KeywordControl('from'), Number,
                         lambda lhs, rhs, i: ForFromType(lhs.variable, rhs))


class ForFromToExpression(BinaryExpression, InterpreterExpression):
    def __init__(self):
        super().__init__(ForFromType, KeywordControl('to'), Number,
                         lambda lhs, rhs, i: ForFromToStepType(lhs.variable, lhs.from_, rhs))


class ForFromToStepExpression(BinaryExpression, InterpreterExpression):
    def __init__(self):
        super().__init__(ForFromToStepType, KeywordControl('step'), Number,
                         lambda lhs, rhs, i: ForFromToStepType(lhs.variable, lhs.from_, lhs.to, rhs))


def _forvar_loop(interpreter, token_name, start, stop, step, code):
    outcome = Nothing
    for i in range(start, stop + 1, step):
        outcome = interpreter.execute_code(code, extra_scope={token_name: Number(i)})
    return outcome


class ForFromToDoExpression(BinaryExpression):
    def __init__(self):
        super().__init__(ForFromToStepType, KeywordControl('do'), Code,
                         lambda lhs, rhs, i: _forvar_loop(
                             i, lhs.variable.value, lhs.from_.value, lhs.to.value, lhs.step.value, rhs))


def _foreach_loop(interpreter, code, elements):
    outcome = Nothing
    for i, x in enumerate(elements):
        outcome = interpreter.execute_code(code, extra_scope={'_x': x, '_forEachIndex': Number(i)})
    return outcome


class ForEachExpression(BinaryExpression):
    def __init__(self):
        super().__init__(Code, KeywordControl('forEach'), Array,
                         lambda lhs, rhs, i: _foreach_loop(i, lhs, rhs.value))


class SwitchExpression(UnaryExpression, InterpreterExpression):
    def __init__(self):
        super().__init__(KeywordControl('switch'), Type,
                         lambda v, i: SwitchType(v))


def parse_switch(interpreter, code):
    conditions = []
    default_used = False

    for statement in code.base_tokens:
        base_tokens = statement.base_tokens
        if not base_tokens:
            pass
        elif base_tokens[0] == KeywordControl('default'):
            if default_used:
                interpreter.exception(SQFSyntaxError(code.position, 'Switch code contains more than 1 `default`'))
            default_used = True
            conditions.append(('default', base_tokens[1]))
        elif base_tokens[0] == KeywordControl('case') and (
                    len(base_tokens) == 2 or
                    len(base_tokens) == 4 and base_tokens[2] == Keyword(':')):
            condition_statement = base_tokens[1]
            if len(base_tokens) == 2:
                outcome_statement = None
            else:
                outcome_statement = base_tokens[3]

            conditions.append((condition_statement, outcome_statement))
        else:
            interpreter.exception(SQFSyntaxError(statement.position, 'Switch code can only start with "case" or "default"'))

    return conditions


def execute_switch(interpreter, result, conditions):
    try:
        default = next(o for c, o in conditions if c == 'default')
    except StopIteration:
        default = None

    final_outcome = None

    execute_next = False
    for condition, outcome in conditions:
        if condition == 'default':
            continue
        condition_outcome = interpreter.value(condition)

        if outcome is not None and execute_next:
            final_outcome = interpreter.execute_code(outcome)
            break
        elif condition_outcome == result:
            if outcome is not None:
                final_outcome = interpreter.execute_code(outcome)
                break
            else:
                execute_next = True

    if final_outcome is None:
        if default is not None:
            final_outcome = interpreter.execute_code(default)
        else:
            final_outcome = Boolean(True)

    return final_outcome


class SwitchDoExpression(BinaryExpression):
    def __init__(self):
        super().__init__(SwitchType, KeywordControl('do'), Code,
                         lambda lhs, rhs, i: execute_switch(i, lhs.result, parse_switch(i, rhs)))


class IfExpression(UnaryExpression, InterpreterExpression):
    def __init__(self):
        super().__init__(KeywordControl('if'), Boolean,
                         lambda v, i: IfType(v))


def _if_then_else(interpreter, condition, then, else_=None):
    if condition:
        result = interpreter.execute_code(then)
    else:
        if else_ is not None:
            result = interpreter.execute_code(else_)
        else:
            result = Nothing
    return result


class IfThenExpression(BinaryExpression):
    def __init__(self):
        super().__init__(IfType, KeywordControl('then'), Code,
                         lambda lhs, rhs, i: _if_then_else(i, lhs.condition.value, rhs))


class ElseExpression(BinaryExpression, InterpreterExpression):
    def __init__(self):
        super().__init__(Code, KeywordControl('else'), Code,
                         lambda lhs, rhs, i: ElseType(lhs, rhs))


class IfThenElseExpression(BinaryExpression):
    def __init__(self):
        super().__init__(IfType, KeywordControl('then'), ElseType,
                         lambda lhs, rhs, i: _if_then_else(i, lhs.condition.value, rhs.then, rhs.else_))


class IfThenSpecExpression(BinaryExpression):
    def __init__(self):
        super().__init__(IfType, KeywordControl('then'), Array,
                         lambda lhs, rhs, i: _if_then_else(i, lhs.condition.value, rhs.value[0], rhs.value[1]))


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
    rhs_assignment = rhs_v.value[1]

    scope = interpreter.get_scope(variable_name, namespace_name)
    scope[variable_name] = rhs_assignment
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


EXPRESSIONS = [
    ForEachExpression(),
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

    IfExpression(),
    ElseExpression(),
    IfThenSpecExpression(),
    IfThenElseExpression(),
    IfThenExpression(),

    # Unary
    UnaryExpression(Keyword('-'), Number, lambda rhs_v, i: Number(-rhs_v.value)),
    UnaryExpression(Keyword('floor'), Number, lambda rhs_v, i: Number(math.floor(rhs_v.value))),
    UnaryExpression(Keyword('reverse'), Array, lambda rhs_v, i: rhs_v.reverse()),
    # Binary
    BinaryExpression(Array, Keyword('set'), Array, lambda lhs_v, rhs_v, i: lhs_v.set(rhs_v)),

    # Array related
    BinaryExpression(Array, Keyword('resize'), Number, lambda lhs_v, rhs_v, i: lhs_v.resize(rhs_v.value)),
    UnaryExpression(Keyword('count'), Array, lambda rhs_v, i: Number(len(rhs_v.value))),
    BinaryExpression(Type, Keyword('in'), Array, lambda lhs_v, rhs_v, i: Boolean(lhs_v in rhs_v.value)),

    BinaryExpression(Array, Keyword('select'), (Number, Boolean), lambda lhs_v, rhs_v, i: lhs_v.value[int(round(rhs_v.value))]),
    BinaryExpression(Array, Keyword('select'), Array, _select_array),

    BinaryExpression(Array, Keyword('find'), Type, _find),
    BinaryExpression(String, Keyword('find'), String, lambda lhs_v, rhs_v, i: Number(lhs_v.value.find(rhs_v.value))),

    BinaryExpression(Array, Keyword('pushBack'), Type, _pushBack),
    BinaryExpression(Array, Keyword('pushBackUnique'), Type, _pushBackUnique),
    BinaryExpression(Array, Keyword('append'), Array, lambda lhs_v, rhs_v, i: lhs_v.add(rhs_v.value)),

    UnaryExpression(Keyword('toArray'), String, lambda rhs_v, i: Array([Number(ord(s)) for s in rhs_v.value])),
    UnaryExpression(Keyword('toString'), Array, lambda rhs_v, i: String('"'+''.join(chr(s.value) for s in rhs_v.value)+'"')),

    # code and namespaces
    UnaryExpression(Keyword('call'), Code, lambda rhs_v, i: i.execute_code(rhs_v)),
    BinaryExpression(Array, Keyword('call'), Code, lambda lhs_v, rhs_v, i: i.execute_code(rhs_v, params=lhs_v)),

    BinaryExpression(Namespace, Keyword('setVariable'), Array, _setVariable,
                     tests=[lambda values: len(values[2].value) in [2,3],
                            lambda values: type(values[2].value[0]) == String]),

    BinaryExpression(Namespace, Keyword('getVariable'), String, _getVariableString),
    BinaryExpression(Namespace, Keyword('getVariable'), Array, _getVariableArray,
                     tests=[lambda values: len(values[2].value) == 2,
                            lambda values: type(values[2].value[0]) == String]),

    BinaryExpression(String, Keyword('addPublicVariableEventHandler'), Code, _addPublicVariableEventHandler),

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
    EXPRESSIONS.append(ComparisonExpression(operator))
for operator in OP_ARITHMETIC:
    EXPRESSIONS.append(ArithmeticExpression(operator))
for operator in OP_LOGICAL:
    EXPRESSIONS.append(LogicalExpression(operator))
