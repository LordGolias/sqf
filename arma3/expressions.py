from arma3.types import Number, Array, Code, Type, Boolean, String, Nothing, Namespace, Variable
from arma3.operators import OPERATORS, OP_COMPARISON, OP_OPERATIONS, OP_ARITHMETIC, OP_ARRAY_OPERATIONS, OP_LOGICAL
from arma3.exceptions import ExecutionError
import math


class Expression:

    def __init__(self, length, action, tests):
        self.length = length
        self.tests = tests
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
        raise NotImplementedError


class UnaryExpression(Expression):
    def __init__(self, op_name, rhs_type, action, tests=None):
        self._op_name = op_name

        if tests is None:
            tests = []
        super().__init__(2, action, [
            lambda values: values[0] == OPERATORS[op_name],
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
            lambda values: values[1] == OPERATORS[op_name],
            lambda values: isinstance(values[0], lhs_type),
            lambda values: isinstance(values[2], rhs_type),
            ] + tests)

    def execute(self, tokens, values, interpreter):
        lhs_v = values[0]
        rhs_v = values[2]
        return self.action(lhs_v, rhs_v, interpreter)


class ComparisonExpression(BinaryExpression):

    def __init__(self, op_name):
        assert(OPERATORS[op_name] in OP_COMPARISON)
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
        op = OPERATORS[op_name]
        assert (op in OP_ARITHMETIC)
        tests = [lambda values: type(values[0]) == type(values[2]) == Array and
                                op in (OPERATORS['+'], OPERATORS['-']) or
                                type(values[0]) == type(values[2]) == String and
                                op == OPERATORS['+'] or
                                type(values[0]) == type(values[2]) == Number]
        super().__init__(op.op, Type, Type, tests=tests)

    def execute(self, tokens, values, _):
        lhs_v = values[0]
        op = values[1]
        rhs_v = values[2]
        lhs_t = type(values[0])
        if type(lhs_v) == Array:
            return Array(OP_ARRAY_OPERATIONS[op](lhs_v.value, rhs_v.value))
        else:
            return lhs_t(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))


class LogicalExpression(BinaryExpression):
    def __init__(self, op_name):
        assert (OPERATORS[op_name] in OP_LOGICAL)

        tests = [lambda values: type(values[0]) == type(values[2]) == Boolean]
        super().__init__(op_name, Type, Type, tests=tests)

    def execute(self, tokens, values, _):
        lhs_v = values[0]
        op = values[1]
        rhs_v = values[2]
        return Boolean(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))


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
    lhs_v.value.append(rhs_v)
    return Number(len(lhs_v.value) - 1)


def _pushBackUnique(lhs_v, rhs_v, _):
    if rhs_v in lhs_v.value:
        return Number(-1)
    else:
        lhs_v.value.append(rhs_v)
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


EXPRESSIONS = [
    # Unary
    UnaryExpression('floor', Number, lambda rhs_v, i: Number(math.floor(rhs_v.value))),
    UnaryExpression('reverse', Array, lambda rhs_v, i: rhs_v.reverse()),
    UnaryExpression('call', Code, lambda rhs_v, i: i.execute_code(rhs_v)),
    UnaryExpression('createMarker', Array, lambda rhs_v, i: i.create_marker(rhs_v)),
    # Binary
    BinaryExpression('set', Array, Array, lambda lhs_v, rhs_v, i: lhs_v.set(rhs_v)),

    # Array related
    BinaryExpression('in', Type, Array, lambda lhs_v, rhs_v, i: Boolean(lhs_v in rhs_v.value)),

    BinaryExpression('select', Array, (Number, Boolean), lambda lhs_v, rhs_v, i: lhs_v.value[int(round(rhs_v.value))]),
    BinaryExpression('select', Array, Array, _select_array),

    BinaryExpression('find', Array, Type, _find),
    BinaryExpression('find', String, String, lambda lhs_v, rhs_v, i: Number(lhs_v.value.find(rhs_v.value))),

    BinaryExpression('pushBack', Array, Type, _pushBack),
    BinaryExpression('pushBackUnique', Array, Type, _pushBackUnique),
    BinaryExpression('append', Array, Array, lambda lhs_v, rhs_v, i: lhs_v.add(rhs_v.value)),

    # code and namespaces
    BinaryExpression('call', Array, Code, lambda lhs_v, rhs_v, i: i.execute_code(rhs_v, params=lhs_v)),
    BinaryExpression('setVariable', Namespace, Array, _setVariable, tests=[lambda values: len(values[2].value) == 2]),

    BinaryExpression('getVariable', Namespace, String, _getVariableString),
    BinaryExpression('getVariable', Namespace, Array, _getVariableArray,
                     tests=[lambda values: len(values[2].value) == 2]),

    BinaryExpression('addPublicVariableEventHandler', String, Code, _addPublicVariableEventHandler),
]

for operator in OP_COMPARISON:
    EXPRESSIONS.append(ComparisonExpression(operator.op))
for operator in OP_ARITHMETIC:
    EXPRESSIONS.append(ArithmeticExpression(operator.op))
for operator in OP_LOGICAL:
    EXPRESSIONS.append(LogicalExpression(operator.op))
