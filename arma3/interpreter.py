from arma3.types import Statement, Code, ConstantValue, Number, Boolean, Nothing, Variable, Array, String, \
    IfToken, ThenToken, ElseToken, WhileToken, DoToken, ForToken, FromToken, ToToken, StepToken, ReservedToken, Type
from arma3.object import Marker
from arma3.operators import Operator, OPERATORS
from arma3.parser import parse
from arma3.exceptions import WrongTypes, IfThenSyntaxError, ExecutionError
from arma3.expressions import EXPRESSIONS
from arma3.namespace import Namespace


class Interpreter:

    def __init__(self, all_vars=None):
        # the stack of scopes. The outermost also contains global variables
        self._namespaces = {
            'uiNamespace': Namespace(),
            'parsingNamespace': Namespace(),
            'missionNamespace': Namespace(all_vars),
            'profileNamespace': Namespace()
        }

        self._current_namespace = self._namespaces['missionNamespace']
        # self._stack = [Scope(all_vars)]

        self._markers = {}

        self._simulation = None
        self._client = None

    @property
    def client(self):
        if self._client is None:
            raise ExecutionError('Trying to access client without a client')
        return self._client

    @client.setter
    def client(self, client):
        self._client = client
        self._simulation = client.simulation

    @property
    def simulation(self):
        if self._simulation is None:
            raise ExecutionError('Trying to access simulation without a simulation assigned')
        return self._simulation

    def set_global_variable(self, var_name, value):
        assert(isinstance(value, Type))
        self._namespaces['missionNamespace'].base_scope[var_name] = value

    @property
    def namespaces(self):
        return self._namespaces

    @property
    def current_scope(self):
        return self._current_namespace.current_scope

    @property
    def values(self):
        return self.current_scope

    def __getitem__(self, name):
        return self.current_scope[name]

    def __contains__(self, other):
        return other in self.values

    @property
    def markers(self):
        return self._markers

    def value(self, token, namespace_name=None):
        if isinstance(token, Variable):
            scope = self.get_scope(token.name, namespace_name)
            return scope[token.name]
        elif isinstance(token, (ConstantValue, Array, Code, Operator, ReservedToken)):
            return token
        else:
            raise NotImplementedError(repr(token))

    def execute_token(self, token):
        """
        Given a single token, recursively evaluate it and return its value.
        """
        # interpret the statement recursively
        if isinstance(token, Statement):
            result = self.execute(statement=token)
        elif token == OPERATORS['isServer']:
            result = Boolean(self.client.is_server)
        elif token == OPERATORS['isClient']:
            result = Boolean(self.client.is_client)
        elif token == OPERATORS['isDedicated']:
            result = Boolean(self.client.is_dedicated)
        else:
            result = token

        return result, self.value(result)

    def get_scope(self, name, namespace_name=None):
        if namespace_name is None:
            namespace = self._current_namespace
        else:
            namespace = self._namespaces[namespace_name]
        return namespace.get_scope(name)

    def add_scope(self, vars=None):
        self._current_namespace.add_scope(vars)

    def del_scope(self):
        self._current_namespace.del_scope()

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

        # evalute the types of all tokens
        values = []
        tokens = []
        types = []
        for token in statement.tokens:
            t, v = self.execute_token(token)
            values.append(v)
            tokens.append(t)
            types.append(type(v))

        case_found = None
        for case in EXPRESSIONS:
            if case.is_match(values):
                case_found = case
                break

        if case_found is not None:
            outcome = case_found.execute(tokens, values, self)
        # todo: replace all elif below by expressions
        elif len(tokens) == 2 and tokens[0] == OPERATORS['publicVariable']:
            if isinstance(tokens[1], String) and not tokens[1].value.startswith('_'):
                var_name = tokens[1].value
                scope = self.get_scope(var_name, 'missionNamespace')
                self.simulation.broadcast(var_name, scope[var_name])
            else:
                raise WrongTypes()
        elif len(tokens) == 2 and tokens[0] == OPERATORS['publicVariableServer']:
            if isinstance(tokens[1], String) and not tokens[1].value.startswith('_'):
                var_name = tokens[1].value
                scope = self.get_scope(var_name, 'missionNamespace')
                if self.simulation:
                    self.simulation.broadcast(var_name, scope[var_name], -1)  # -1 => to server
                else:
                    raise ExecutionError('Interpreter called "publicVariable" without a simulation.')
            else:
                raise WrongTypes()
        elif len(tokens) == 2 and tokens[0] == OPERATORS['private']:
            if isinstance(statement.tokens[1], String):
                self.add_privates([tokens[1].value])
            elif isinstance(statement.tokens[1], Array):
                self.add_privates([s.value for s in tokens[1].value])
            elif isinstance(statement.tokens[1], Statement) and len(statement.tokens[1]) == 3 and \
                 isinstance(statement.tokens[1][0], Variable) and statement.tokens[1][1] == OPERATORS['=']:
                self.add_privates([statement.tokens[1][0].name])
                outcome = self.execute(statement.tokens[1])
            else:
                raise SyntaxError()
        # binary operators
        elif len(tokens) == 3 and isinstance(tokens[1], Operator):
            # it is a binary statement: token, operation, token
            lhs = tokens[0]
            lhs_v = values[0]
            lhs_t = types[0]

            op = tokens[1]
            rhs = tokens[2]
            rhs_v = values[2]
            rhs_t = types[2]

            if op == OPERATORS['=']:
                if not isinstance(lhs, Variable):
                    raise WrongTypes(repr(lhs))
                if not isinstance(rhs_v, Type):
                    raise WrongTypes(repr(rhs))

                variable_scope = self.get_scope(lhs.name)
                variable_scope[lhs.name] = rhs_v
                outcome = rhs
            elif op == OPERATORS['publicVariableClient']:
                if lhs_t == Number and not rhs.value.startswith('_'):
                    client_id = lhs.value
                    var_name = rhs.value
                    scope = self.get_scope(var_name, 'missionNamespace')
                    if self.simulation:
                        self.simulation.broadcast(var_name, scope[var_name], client_id)
                    else:
                        raise ExecutionError('Interpreter called "publicVariable" without a simulation.')
                else:
                    raise WrongTypes()
            else:
                raise NotImplementedError([lhs, op, rhs])
        # code, variables and values
        elif len(tokens) == 1 and isinstance(tokens[0], (Code, ConstantValue, Variable)):
            outcome = values[0]
        # if then else
        elif len(tokens) >= 4 and tokens[0] == IfToken and (isinstance(tokens[1], Statement) and
                tokens[1].parenthesis or isinstance(tokens[1], Boolean)) and tokens[2] == ThenToken:
            condition_outcome = values[1]
            if isinstance(condition_outcome, Boolean):
                if condition_outcome.value is True:
                    _then = True
                else:
                    _then = False
            else:
                raise WrongTypes('If condition must be a Boolean')

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

    def create_marker(self, rhs_v):
        name = rhs_v.value[0].value
        if name in self._markers:
            raise ExecutionError('Marker "%s" already exists' % name)
        pos = rhs_v.value[1]
        if not isinstance(pos, Array):
            raise WrongTypes('Second argument of "createMarker" must be a position')
        self._markers[name] = Marker(pos)
        return rhs_v.value[0]


def interpret(script, interpreter=None):
    if interpreter is None:
        interpreter = Interpreter()
    assert(isinstance(interpreter, Interpreter))

    statements = parse(script)

    outcome = Nothing
    for statement in statements:
        outcome = interpreter.execute(statement)

    return interpreter, outcome
