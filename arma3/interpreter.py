from arma3.types import Statement, Code, ConstantValue, Number, Boolean, Nothing, Variable, Array, String, \
    ReservedToken, Type
from arma3.object import Marker
from arma3.operators import Operator, OPERATORS
from arma3.parser import parse
from arma3.exceptions import WrongTypes, ExecutionError
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

    def get_variable(self, token):
        if isinstance(token, Statement):
            return token.base_tokens[0]
        else:
            if not isinstance(token, Variable):
                raise SyntaxError('This operator requires a variable')
            return token

    def execute_token(self, token):
        """
        Given a single token, recursively evaluate it and return its value.
        """
        # interpret the statement recursively
        if isinstance(token, Statement):
            result = self._execute(statement=token)
        elif isinstance(token, Array):
            # empty statements are ignored
            result = Array([self.execute_token(s)[1] for s in token.value if s])
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
        for statement in code.base_tokens:
            outcome = self._execute(statement)
        self.del_scope()
        return outcome

    def _execute(self, statement):
        assert(not isinstance(statement, Code))

        outcome = Nothing

        # evaluate the types of all tokens
        base_tokens = statement.base_tokens
        values = []
        tokens = []
        types = []

        for token in statement.base_tokens:
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

            if isinstance(values[1], String):
                self.add_privates([values[1].value])
            elif isinstance(values[1], Array):
                self.add_privates([s.value for s in values[1].value])
            elif isinstance(base_tokens[1], Statement) and len(base_tokens[1]) == 3 and \
                base_tokens[1][1] == OPERATORS['=']:
                variable = self.get_variable(base_tokens[1][0])

                self.add_privates([variable.name])
                outcome = self._execute(base_tokens[1])
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
                lhs = self.get_variable(base_tokens[0])

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
        elif len(tokens) == 1 and isinstance(tokens[0], (Code, ConstantValue, ReservedToken, Variable, Array)):
            outcome = values[0]
        else:
            raise NotImplementedError('Interpretation of "%s" not implemented' % tokens)

        if statement.ending:
            outcome = Nothing
        return outcome

    def execute(self, statements):
        outcome = Nothing
        for statement in statements:
            outcome = self._execute(statement)
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

    outcome = interpreter.execute(statements)

    return interpreter, outcome
