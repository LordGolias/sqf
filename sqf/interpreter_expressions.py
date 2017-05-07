import math

from sqf.types import Keyword, Namespace, Number, Array, Code, Type, Boolean, String, Nothing, Variable
from sqf.interpreter_types import WhileType, ForType, ForSpecType, SwitchType, IfType, ElseType, TryType
from sqf.exceptions import SQFParserError
from sqf.keywords import OP_ARITHMETIC, OP_COMPARISON, OP_LOGICAL
from sqf.expressions import BinaryExpression, UnaryExpression


OP_OPERATIONS = {
    # Arithmetic
    Keyword('+'): lambda x, y: x + y,
    Keyword('-'): lambda x, y: x - y,
    Keyword('*'): lambda x, y: x * y,
    Keyword('/'): lambda x, y: x / y,
    Keyword('%'): lambda x, y: x % y,
    Keyword('mod'): lambda x, y: x % y,
    Keyword('^'): lambda x, y: x ** y,
    Keyword('max'): lambda x, y: max(x, y),
    Keyword('floor'): lambda x: math.floor(x),

    # Comparison
    Keyword('=='): lambda x, y: x == y,
    Keyword('!='): lambda x, y: x != y,
    Keyword('<'): lambda x, y: x < y,
    Keyword('>'): lambda x, y: x < y,
    Keyword('<='): lambda x, y: x <= y,
    Keyword('>='): lambda x, y: x >= y,

    # Logical
    Keyword('&&'): lambda x, y: x and y,
    Keyword('and'): lambda x, y: x and y,
    Keyword('||'): lambda x, y: x or y,
    Keyword('or'): lambda x, y: x or y,
}


class ComparisonExpression(BinaryExpression):

    def __init__(self, op, lhs_rhs_type):
        assert(op in OP_COMPARISON)
        assert (issubclass(lhs_rhs_type, Type))
        super().__init__(lhs_rhs_type, op, lhs_rhs_type, Boolean, self._action)

    def _action(self, lhs, rhs, _):
        if lhs.value is None or rhs.value is None:
            return None
        return OP_OPERATIONS[self.keyword](lhs.value, rhs.value)


class ArithmeticExpression(BinaryExpression):

    def __init__(self, op):
        assert (op in OP_ARITHMETIC)
        super().__init__(Number, op, Number, Number, self._action)

    def _action(self, lhs, rhs, _):
        if lhs.value is None or rhs.value is None:
            return None
        return OP_OPERATIONS[self.keyword](lhs.value, rhs.value)


class LogicalExpression(BinaryExpression):
    def __init__(self, op):
        assert (op in OP_LOGICAL)
        super().__init__(Boolean, op, Boolean, Boolean, self._action)

    def _action(self, lhs, rhs, _):
        if lhs.value is None or rhs.value is None:
            return None
        return OP_OPERATIONS[self.keyword](lhs.value, rhs.value)


def _while_loop(interpreter, condition_code, do_code):
    outcome = Nothing()
    while True:
        condition_outcome = interpreter.execute_code(condition_code)
        if condition_outcome.value is False:
            break
        outcome = interpreter.execute_code(do_code)
    return outcome


class WhileExpression(UnaryExpression):
    """
    Catches `While {}` expression and stores it as a WhileType
    """
    def __init__(self):
        super().__init__(Keyword('while'), Code, WhileType, lambda v, i: v)


class WhileDoExpression(BinaryExpression):
    def __init__(self):
        super().__init__(WhileType, Keyword('do'), Code, None,
                         lambda lhs, rhs, i: _while_loop(i, lhs.condition, rhs))


def _forspecs_type(array, interpreter):
    if len(array) != 3:
        interpreter.exception(SQFParserError(
            array.position, 'for-then array must contain 3 elements (contains %d)' % len(array)))
        return None
    return array


class ForSpecExpression(UnaryExpression):
    def __init__(self):
        super().__init__(Keyword('for'), Array, ForSpecType, _forspecs_type)


def _forspecs_loop(interpreter, start_code, stop_code, increment_code, do_code):
    outcome = Nothing()
    outcome.position = start_code.position

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
        super().__init__(ForSpecType, Keyword('do'), Code, None,
                         lambda lhs, rhs, i: _forspecs_loop(i, lhs.array[0], lhs.array[1], lhs.array[2], rhs))


class ForExpression(UnaryExpression):
    def __init__(self):
        super().__init__(Keyword('for'), String, ForType, lambda rhs, i: rhs)


class ForFromExpression(BinaryExpression):
    def __init__(self):
        super().__init__(ForType, Keyword('from'), Number, ForType,
                         lambda lhs, rhs, i: (lhs.variable, rhs))


class ForFromToExpression(BinaryExpression):
    def __init__(self):
        super().__init__(ForType, Keyword('to'), Number, ForType,
                         lambda lhs, rhs, i: (lhs.variable, lhs.from_, rhs))


class ForFromToStepExpression(BinaryExpression):
    def __init__(self):
        super().__init__(ForType, Keyword('step'), Number, ForType,
                         lambda lhs, rhs, i: (lhs.variable, lhs.from_, lhs.to, rhs))


def _forvar_loop(interpreter, token_name, start, stop, step, code):
    outcome = Nothing()
    outcome.position = code.position

    for i in range(start, stop + 1, step):
        outcome = interpreter.execute_code(code, extra_scope={token_name: Number(i)})
    return outcome


class ForFromToDoExpression(BinaryExpression):
    def __init__(self):
        super().__init__(ForType, Keyword('do'), Code, None,
                         lambda lhs, rhs, i: _forvar_loop(
                             i, lhs.variable.value, lhs.from_.value, lhs.to.value, lhs.step.value, rhs))


def _foreach_loop(interpreter, code, elements):
    outcome = Nothing()
    for i, x in enumerate(elements):
        outcome = interpreter.execute_code(code, extra_scope={'_x': x, '_forEachIndex': Number(i)})
    return outcome


class ForEachExpression(BinaryExpression):
    def __init__(self):
        super().__init__(Code, Keyword('forEach'), Array, None,
                         lambda lhs, rhs, i: _foreach_loop(i, lhs, rhs.value))


class SwitchExpression(UnaryExpression):
    def __init__(self):
        super().__init__(Keyword('switch'), Type, SwitchType, lambda v, i: v)


class CaseExpression(UnaryExpression):
    def __init__(self):
        super().__init__(Keyword('case'), Type, SwitchType, lambda v, i: v)


def parse_switch(interpreter, code):
    conditions = []
    default_used = False

    for statement in code.base_tokens:
        base_tokens = statement.base_tokens

        # evaluate all the base_tokens, trying to obtain their values
        values = []
        for token in base_tokens:
            v = interpreter.value(token)
            values.append(v)

        if CaseExpression().is_match(values):
            values = [CaseExpression().execute(values, interpreter)]

        if values[0] == Keyword('default'):
            if default_used:
                interpreter.exception(SQFParserError(code.position, 'Switch code contains more than 1 `default`'))
            default_used = True
            if len(values) == 2:
                if isinstance(values[1], (Variable, Code)):
                    conditions.append(('default', values[1]))
                else:
                    interpreter.exception(
                        SQFParserError(base_tokens[1].position, '"default" 2nd argument must be code'))
            else:
                interpreter.exception(
                    SQFParserError(base_tokens[1].position, '"default" must contain 2 clauses'))
        elif type(values[0]) == SwitchType:
            case_condition = values[0].result
            if len(values) == 1:
                conditions.append((case_condition, None))
            elif len(values) == 3:
                if values[1] == Keyword(':'):
                    outcome_statement = values[2]
                    conditions.append((case_condition, outcome_statement))
                else:
                    interpreter.exception(
                        SQFParserError(base_tokens[1].position, '"case" second argument must be ":"'))
            else:
                interpreter.exception(
                    SQFParserError(statement.position, '"case" must be a 2 or 4 statement'))
        elif values[0] == Keyword('case'):
            interpreter.exception(
                SQFParserError(statement.position, 'keyword "case" must be followed by an argument'))
        else:
            interpreter.exception(SQFParserError(statement.position, 'Switch code can only start with "case" or "default"'))

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
        super().__init__(SwitchType, Keyword('do'), Code, None,
                         lambda lhs, rhs, i: execute_switch(i, lhs.result, parse_switch(i, rhs)))


class IfExpression(UnaryExpression):
    def __init__(self):
        super().__init__(Keyword('if'), Boolean, IfType, lambda v, i: v)


def _if_then_else(interpreter, condition, then, else_=None):
    if condition:
        result = interpreter.execute_code(then)
    else:
        if else_ is not None:
            result = interpreter.execute_code(else_)
        else:
            result = Nothing()
    return result


class IfThenExpression(BinaryExpression):
    def __init__(self):
        super().__init__(IfType, Keyword('then'), Code, None,
                         lambda lhs, rhs, i: _if_then_else(i, lhs.condition.value, rhs))


class ElseExpression(BinaryExpression):
    def __init__(self):
        super().__init__(Code, Keyword('else'), Code, ElseType, lambda lhs, rhs, i: (lhs, rhs))


class IfThenElseExpression(BinaryExpression):
    def __init__(self):
        super().__init__(IfType, Keyword('then'), ElseType, None,
                         lambda lhs, rhs, i: _if_then_else(i, lhs.condition.value, rhs.then, rhs.else_))


class IfThenSpecExpression(BinaryExpression):
    def __init__(self):
        super().__init__(IfType, Keyword('then'), Array, None,
                         lambda lhs, rhs, i: _if_then_else(i, lhs.condition.value, rhs.value[0], rhs.value[1]))


class IfThenExitWithExpression(BinaryExpression):
    def __init__(self):
        super().__init__(IfType, Keyword('exitwith'), Code, Nothing,
                         lambda lhs, rhs, i: None)  # todo: implement this in the interpreter


def _try_catch(interpreter, try_code, catch_code):
    result = interpreter.execute_code(try_code)
    # todo: find a way to execute catch_code on error
    interpreter.execute_code(catch_code, extra_scope={'_exception': Nothing()})
    return result


class TryExpression(UnaryExpression):
    def __init__(self):
        super().__init__(Keyword('try'), Code, TryType, lambda v, i: v)


class TryCatchExpression(BinaryExpression):
    def __init__(self):
        super().__init__(TryType, Keyword('catch'), Code, None,
                         lambda lhs, rhs, i: _try_catch(i, lhs.code, rhs))


def _select(lhs, rhs, interpreter):
    if lhs.value is None or rhs.value is None:
        return Nothing()

    index = int(round(rhs.value))
    try:
        return lhs[index]
    except IndexError:
        interpreter.exception(SQFParserError(
            lhs.position, 'selecting element %d of array of size %d' % (index, len(lhs))))
        return Nothing()


def _select_array(lhs, rhs, interpreter):
    if lhs.value is None or rhs.value is None:
        return []
    start = rhs.value[0].value
    count = rhs.value[1].value

    if start > len(lhs.value):
        interpreter.exception(SQFParserError(lhs.position, 'Selecting element past size'))
        return []

    return lhs.value[start:start + count]


def _subtract_arrays(lhs, rhs):
    rhs_set = set([rhs_i.value for rhs_i in rhs.value])
    return [lhs_i for lhs_i in lhs if lhs_i.value not in rhs_set]


def _find(lhs_v, rhs_v):
    try:
        index = next(i for i, v in enumerate(lhs_v.value) if v == rhs_v)
    except StopIteration:
        index = -1
    return index


def _pushBack(lhs_v, rhs_v):
    lhs_v.append(rhs_v)
    return len(lhs_v.value) - 1


def _pushBackUnique(lhs_v, rhs_v):
    if rhs_v in lhs_v.value:
        return -1
    else:
        lhs_v.append(rhs_v)
        return len(lhs_v.value) - 1


def _setVariable(lhs_v, rhs_v, interpreter):
    if lhs_v.value is None or rhs_v.value is None:
        return
    namespace_name = lhs_v.value
    assert(isinstance(rhs_v, Array))

    if len(rhs_v) not in [2, 3]:
        interpreter.exception(SQFParserError(
            lhs_v.position, 'setVariable requires array of 2-3 elements (has %d)' % (len(rhs_v))))
        return

    # get the variable name
    if not isinstance(rhs_v.value[0], (String, Nothing)):
        interpreter.exception(SQFParserError(
            lhs_v.position, 'setVariable array first element must be a string (is %s)' % type(rhs_v.value[0]).__name__))
        return

    variable_name = rhs_v.value[0].value
    # get the value
    rhs_assignment = rhs_v.value[1]
    if variable_name is None:
        return

    scope = interpreter.get_scope(variable_name, namespace_name)
    scope[variable_name] = rhs_assignment


def _getVariableString(lhs_v, rhs_v, interpreter):
    if lhs_v.value is None or rhs_v.value is None:
        return Nothing()
    variable = Variable(rhs_v.value)
    variable.position = rhs_v.position
    return interpreter.value(variable, lhs_v.value)


def _getVariableArray(lhs_v, rhs_v, interpreter):
    if lhs_v.value is None or rhs_v.value is None or rhs_v.value[0].value is None:
        return Nothing()
    # get the variable name
    if len(rhs_v) != 2:
        interpreter.exception(SQFParserError(
            lhs_v.position, 'getVariable requires array of 2 elements (has %d)' % (len(rhs_v))))
        return Nothing()

    if not isinstance(rhs_v.value[0], (String, Nothing)):
        interpreter.exception(SQFParserError(
            lhs_v.position,
            'getVariable array first element must be a string (is %s)' % type(rhs_v.value[0]).__name__))
        return Nothing()

    variable = Variable(rhs_v.value[0].value)
    variable.position = rhs_v.value[0].position
    outcome = interpreter.value(variable, lhs_v.value)
    if outcome == Nothing():
        outcome = rhs_v.value[1]
    return outcome


def _addPublicVariableEventHandler(lhs_v, rhs_v, interpreter):
    interpreter.client.add_listening(lhs_v.value, rhs_v)


class Action:
    def __init__(self, action):
        self.action = action

    def __call__(self, *args):
        result = None
        # interpreter = args[-1]
        all_args = args[:-1]

        can_execute = True
        for arg in all_args:
            if arg.value is None or isinstance(arg, Array) and any(x.value is None for x in arg.value):
                can_execute = False
                break

        if can_execute:
            result = self.action(*all_args)
        return result


EXPRESSIONS = [
    CaseExpression(),

    TryExpression(),
    TryCatchExpression(),

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
    IfThenExitWithExpression(),

    # params
    UnaryExpression(Keyword('params'), Array, Nothing, lambda rhs_v, i: i.add_params(rhs_v)),
    BinaryExpression(Type, Keyword('params'), Array, Nothing, lambda lhs_v, rhs_v, i: i.add_params(rhs_v)),

    # Unary
    UnaryExpression(Keyword('-'), Number, Number, Action(lambda x: -x.value)),
    UnaryExpression(Keyword('floor'), Number, Number, Action(lambda x: math.floor(x.value))),
    UnaryExpression(Keyword('reverse'), Array, Nothing, Action(lambda rhs_v: rhs_v.reverse())),
    # Binary
    BinaryExpression(Array, Keyword('set'), Array,
                     Nothing, Action(lambda lhs_v, rhs_v: lhs_v.set(rhs_v))),

    # Array related
    BinaryExpression(Array, Keyword('resize'), Number,
                     Nothing, Action(lambda lhs_v, rhs_v: lhs_v.resize(rhs_v.value))),
    UnaryExpression(Keyword('count'), Array, Number, Action(lambda x: len(x.value))),
    BinaryExpression(Type, Keyword('in'), Array, Boolean, Action(lambda x, array: x in array.value)),

    BinaryExpression(Array, Keyword('select'), Number, None, _select),
    BinaryExpression(Array, Keyword('select'), Boolean, None, _select),
    BinaryExpression(Array, Keyword('select'), Array, Array, _select_array),

    BinaryExpression(Array, Keyword('find'), Type, Number, Action(_find)),
    BinaryExpression(String, Keyword('find'), String, Number,
                     Action(lambda lhs_v, rhs_v: lhs_v.value.find(rhs_v.value))),

    BinaryExpression(Array, Keyword('pushBack'), Type, Number, Action(_pushBack)),
    BinaryExpression(Array, Keyword('pushBackUnique'), Type, Number, Action(_pushBackUnique)),
    BinaryExpression(Array, Keyword('append'), Array, Nothing, Action(lambda lhs_v, rhs_v: lhs_v.add(rhs_v.value))),

    UnaryExpression(Keyword('toArray'), String, Array,
                    Action(lambda rhs_v: [Number(ord(s)) for s in rhs_v.value])),
    UnaryExpression(Keyword('toString'), Array, String,
                    Action(lambda rhs_v: '"'+''.join(chr(s.value) for s in rhs_v.value)+'"')),

    # code and namespaces
    UnaryExpression(Keyword('call'), Code, None, lambda rhs_v, i: i.execute_code(rhs_v)),
    BinaryExpression(Array, Keyword('call'), Code, None, lambda lhs_v, rhs_v, i: i.execute_code(rhs_v, params=lhs_v)),

    BinaryExpression(Namespace, Keyword('setVariable'), Array, Nothing, _setVariable),

    BinaryExpression(Namespace, Keyword('getVariable'), String, None, _getVariableString),
    BinaryExpression(Namespace, Keyword('getVariable'), Array, None, _getVariableArray),

    BinaryExpression(String, Keyword('addPublicVariableEventHandler'), Code, None, _addPublicVariableEventHandler),

    BinaryExpression(Array, Keyword('+'), Array, Array, Action(lambda lhs_v, rhs_v: lhs_v.value + rhs_v.value)),
    BinaryExpression(Array, Keyword('-'), Array, Array, Action(_subtract_arrays)),

    BinaryExpression(String, Keyword('+'), String, String, Action(lambda lhs, rhs: lhs.container + lhs.value + rhs.value + lhs.container)),
]

for op in OP_COMPARISON:
    for lhs_rhs_type in [Number, String]:
        if lhs_rhs_type == Number or lhs_rhs_type == String and op in [Keyword('=='), Keyword('!=')]:
            EXPRESSIONS.append(ComparisonExpression(op, lhs_rhs_type))
for op in OP_ARITHMETIC:
    EXPRESSIONS.append(ArithmeticExpression(op))
for op in OP_LOGICAL:
    EXPRESSIONS.append(LogicalExpression(op))
