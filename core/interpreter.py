from core.types import Statement, Code, ConstantValue, Number, Boolean, Nothing, Variable, Array, String, \
    IfToken, ThenToken, ElseToken, WhileToken, DoToken, ForToken, FromToken, ToToken, StepToken
from core.object import Marker
from core.operators import Operator, OPERATORS, OP_OPERATIONS, OP_ARITHMETIC, OP_ARRAY_OPERATIONS, OP_COMPARISON, OP_LOGICAL
from core.parser import parse
from core.exceptions import WrongTypes, IfThenSyntaxError, ExecutionError


class Scope:

    def __init__(self, values=None):
        if values is None:
            values = {}
        self.values = values

    def __contains__(self, other):
        return other in self.values

    def __getitem__(self, name):
        if name in self.values:
            return self.values[name]
        else:
            return Nothing

    def __setitem__(self, item, value):
        self.values[item] = value


class Interpreter:

    def __init__(self, all_vars=None):
        # the stack of scopes. The outermost also contains global variables
        self._stack = [Scope(all_vars)]

        self._markers = {}

    @property
    def current_scope(self):
        return self._stack[-1]

    @property
    def values(self):
        return self.current_scope.values

    def __getitem__(self, name):
        return self.current_scope[name]

    def __contains__(self, other):
        return other in self.values

    @property
    def markers(self):
        return self._markers

    def value(self, token):
        if isinstance(token, Variable):
            scope = self.get_scope(token.name)
            return scope[token.name]
        elif isinstance(token, (ConstantValue, Array, Code)):
            return token
        else:
            raise NotImplementedError(token)

    def execute_token(self, token):
        """
        Given a single token, recursively evaluate it and return its value.
        """
        # interpret the statement recursively
        if isinstance(token, Statement):
            result = self.execute(statement=token)
        else:
            result = token

        return result, self.value(result)

    def get_scope(self, name):
        if name.startswith('_'):
            for i in reversed(range(1, len(self._stack))):
                scope = self._stack[i]
                if name in scope:
                    return scope
            return self._stack[0]
        else:
            return self._stack[0]

    def add_scope(self, vars=None):
        if vars is None:
            vars = {}
        self._stack.append(Scope(vars))

    def del_scope(self):
        del self._stack[-1]

    def add_privates(self, private_names):
        for name in private_names:
            if name.startswith('_'):
                self.current_scope[name] = Nothing
            else:
                raise SyntaxError('Cannot set variables without "_" as `private`')

    def execute_code(self, code, params=None, extra_scope=None):
        assert (isinstance(code, Code))
        if params is None:
            params = Array([])
        if extra_scope is None:
            extra_scope = {}
        extra_scope['_this'] = params
        self.add_scope(extra_scope)
        outcome = Nothing
        for statement in code.tokens:
            outcome = self.execute(statement)
        self.del_scope()
        return outcome

    def execute(self, statement):
        assert(not isinstance(statement, Code))

        outcome = Nothing
        tokens = statement.tokens

        if len(tokens) == 2 and tokens[0] == OPERATORS['private']:
            if isinstance(tokens[1], String):
                self.add_privates([tokens[1].value])
            elif isinstance(tokens[1], Array):
                self.add_privates([s.value for s in tokens[1].value])
            elif isinstance(tokens[1], Statement) and len(tokens[1]) == 3 and \
                 isinstance(tokens[1][0], Variable) and tokens[1][1] == OPERATORS['=']:
                self.add_privates([tokens[1][0].name])
                outcome = self.execute(tokens[1])
            else:
                raise SyntaxError()
        # binary operators
        elif len(tokens) == 3 and isinstance(tokens[1], Operator):
            # it is a binary statement: token, operation, token
            lhs = tokens[0]
            op = tokens[1]
            rhs = tokens[2]

            # a token has its type (lhs), its return value (lhs_v), and its type (lhs_t)
            lhs, lhs_v = self.execute_token(lhs)
            lhs_t = type(lhs_v)
            rhs, rhs_v = self.execute_token(rhs)
            rhs_t = type(rhs_v)

            if op == OPERATORS['=']:
                if not isinstance(lhs, Variable):
                    raise WrongTypes()

                rhs, rhs_v = self.execute_token(rhs)

                variable_scope = self.get_scope(lhs.name)
                variable_scope[lhs.name] = rhs_v
                outcome = rhs
            elif op in OP_COMPARISON:

                if lhs_t != rhs_t:
                    raise WrongTypes('Comparing wrong types with "==" operator')
                if lhs_t == rhs_t == Boolean:
                    raise WrongTypes('Can not compare between two booleans. Use logical operators.')

                outcome = Boolean(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))
            elif op in OP_ARITHMETIC:
                if lhs_t == rhs_t == Array and op in (OPERATORS['+'], OPERATORS['-']):
                    outcome = Array(OP_ARRAY_OPERATIONS[op](lhs_v.value, rhs_v.value))
                elif lhs_t == rhs_t == Number or lhs_t == rhs_t == String:
                    outcome = lhs_t(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))
                else:
                    raise WrongTypes('Can only use arithmetic operators on numbers')
            elif op in OP_LOGICAL:
                if lhs_t == rhs_t == Boolean:
                    outcome = Boolean(OP_OPERATIONS[op](lhs_v.value, rhs_v.value))
                else:
                    raise WrongTypes('Logical operators require booleans')
            elif op == OPERATORS['set']:
                # https://community.bistudio.com/wiki/set
                if lhs_t == rhs_t == Array:
                    index = rhs_v.value[0].value
                    value = rhs_v.value[1]

                    variable_scope = self.get_scope(lhs.name)
                    if index >= len(lhs_v.value):
                        variable_scope[lhs.name].extend(index)
                    variable_scope[lhs.name].set(index, value)
                    outcome = Nothing
                else:
                    raise WrongTypes('"set" requires two arrays')
            elif op == OPERATORS['in']:
                # https://community.bistudio.com/wiki/in
                if rhs_t == Array:
                    outcome = Boolean(lhs_v in rhs_v.value)
                else:
                    raise NotImplementedError
            elif op == OPERATORS['select']:
                # https://community.bistudio.com/wiki/select
                if lhs_t == Array and rhs_t in (Number, Boolean):
                    index = int(round(rhs_v.value))  # x for value<=x.5 and x+1 for > x.5
                    outcome = lhs_v.value[index]
                elif lhs_t == Array and rhs_t == Array:
                    start = rhs_v.value[0].value
                    count = rhs_v.value[1].value
                    outcome = Array(lhs_v.value[start:start+count])
                # todo: missing the syntax using expressions. This requires delaying the evaluation of the rhs
                else:
                    raise WrongTypes()
            elif op == OPERATORS['find']:
                if lhs_t == Array:
                    try:
                        index = next(i for i,v in enumerate(lhs_v.value) if v == rhs_v)
                    except StopIteration:
                        index = -1
                    outcome = Number(index)
                elif lhs_t == rhs_t == String:
                    outcome = Number(lhs_v.value.find(rhs_v.value))
                else:
                    raise WrongTypes()
            elif op == OPERATORS['pushBack']:
                if lhs_t == Array:
                    lhs_v.value.append(rhs_v)
                    outcome = Number(len(lhs_v.value) - 1)
                else:
                    raise WrongTypes()
            elif op == OPERATORS['pushBackUnique']:
                if lhs_t == Array:
                    if rhs_v in lhs_v.value:
                        outcome = Number(-1)
                    else:
                        lhs_v.value.append(rhs_v)
                        outcome = Number(len(lhs_v.value) - 1)
                else:
                    raise WrongTypes()
            elif op == OPERATORS['append']:
                if lhs_t == rhs_t == Array:
                    lhs_v.add(rhs_v.value)
                    outcome = Nothing
                else:
                    raise WrongTypes()
            elif op == OPERATORS['call']:
                if not isinstance(lhs_v, Array) or not isinstance(rhs_v, Code):
                    raise WrongTypes()
                outcome = self.execute_code(rhs_v, params=lhs_v)
            else:
                raise NotImplementedError([lhs, op, rhs])
        # unary operators
        elif len(tokens) == 2 and isinstance(tokens[0], Operator):
            op = tokens[0]
            rhs = tokens[1]

            # a token has its type (lhs), its return value (lhs_v), and its type (lhs_t)
            rhs, rhs_v = self.execute_token(rhs)
            rhs_t = type(rhs_v)

            if op == OPERATORS['floor']:
                if rhs_t != Number:
                    raise WrongTypes()
                outcome = Number(OP_OPERATIONS[op](rhs_v.value))
            elif op == OPERATORS['reverse']:
                # https://community.bistudio.com/wiki/reverse
                if rhs_t == Array:
                    rhs_v.reverse()
                    outcome = Nothing
                else:
                    raise WrongTypes()
            elif op == OPERATORS['call']:
                if not isinstance(rhs, Code):
                    raise WrongTypes()
                outcome = self.execute_code(rhs)
            elif op == OPERATORS['createMarker']:
                if not rhs_t == Array:
                    raise WrongTypes()
                name = rhs_v.value[0].value
                if name in self._markers:
                    raise ExecutionError('Marker "%s" already exists' % name)
                pos = rhs_v.value[1]
                if not isinstance(pos, Array):
                    raise WrongTypes('Second argument of "createMarker" must be a position')
                self._markers[name] = Marker(pos)
                outcome = rhs_v.value[0]
            else:
                raise NotImplementedError
        # statement
        elif len(tokens) == 1 and isinstance(tokens[0], Statement):
            outcome = self.execute(tokens[0])
        # code, variables and values
        elif len(tokens) == 1 and isinstance(tokens[0], (Code, ConstantValue, Variable)):
            outcome = self.execute_token(tokens[0])[1]
        # if then else
        elif len(tokens) >= 4 and tokens[0] == IfToken and (isinstance(tokens[1], Statement) and
                tokens[1].parenthesis or isinstance(tokens[1], Boolean)) and tokens[2] == ThenToken:
            condition_outcome = self.execute_token(tokens[1])[1]
            if isinstance(condition_outcome, Boolean):
                if condition_outcome.value is True:
                    _then = True
                else:
                    _then = False
            else:
                raise WrongTypes('If condition must return a Boolean')

            if len(tokens) == 4 and isinstance(tokens[3], Code):
                if _then:
                    outcome = self.execute_code(tokens[3])
            elif len(tokens) == 4 and isinstance(tokens[3], Array) and \
                    len(tokens[3].value) == 2 and isinstance(tokens[3].value[0], Code) and isinstance(tokens[3].value[1], Code):
                if _then:
                    outcome = self.execute_code(tokens[3].value[0])
                else:
                    outcome = self.execute_code(tokens[3].value[1])
            elif len(tokens) == 6 and isinstance(tokens[3], Code) and tokens[4] == ElseToken and isinstance(tokens[5], Code):
                if _then:
                    outcome = self.execute_code(tokens[3])
                else:
                    outcome = self.execute_code(tokens[5])
            else:
                raise IfThenSyntaxError()
        # While loop
        elif len(tokens) == 4 and tokens[0] == WhileToken and isinstance(tokens[1], Code) and \
                tokens[2] == DoToken and isinstance(tokens[3], Code):
            while True:
                condition_outcome = self.execute_code(tokens[1])
                if condition_outcome.value is False:
                    break
                outcome = self.execute_code(tokens[3])
        # forspecs loop
        elif len(tokens) == 4 and tokens[0] == ForToken and isinstance(tokens[1], Array) and \
                tokens[2] == DoToken and isinstance(tokens[3], Code):
            start = tokens[1].value[0]
            stop = tokens[1].value[1]
            do = tokens[3]
            increment = tokens[1].value[2]

            self.execute_code(start)
            while True:
                condition_outcome = self.execute_code(stop)
                if condition_outcome.value is False:
                    break

                outcome = self.execute_code(do)
                self.execute_code(increment)
        # forvar loop
        elif len(tokens) >= 8 and \
                tokens[0] == ForToken and \
                isinstance(tokens[1], String) and \
                tokens[2] == FromToken and \
                isinstance(tokens[3], Number) and \
                tokens[4] == ToToken and \
                isinstance(tokens[5], Number) and \
                tokens[-2] == DoToken and isinstance(tokens[-1], Code):
            if len(tokens) == 8:
                step = 1
            elif len(tokens) == 10 and tokens[6] == StepToken and isinstance(tokens[7], Number):
                step = tokens[7].value
            else:
                raise SyntaxError()

            start = tokens[3].value
            stop = tokens[5].value
            code = tokens[-1]

            for i in range(start, stop + 1, step):
                outcome = self.execute_code(code, extra_scope={tokens[1].value: Number(i)})
        else:
            raise NotImplementedError('Interpretation of "%s" not implemented' % tokens)

        if statement.ending:
            outcome = Nothing
        return outcome


def interpret(script):
    statements = parse(script)

    interpreter = Interpreter()

    outcome = Nothing
    for statement in statements:
        outcome = interpreter.execute(statement)

    return interpreter, outcome
