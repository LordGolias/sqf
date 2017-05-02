from sqf.types import Statement, Code, ConstantValue, Number, Nothing, Variable, Array, String, Type
from sqf.interpreter_types import InterpreterType
from sqf.keywords import Keyword
from sqf.exceptions import SQFSyntaxError
from sqf.namespace import Namespace


class BaseInterpreter:
    """
    Base Interpreter used by the analyzer and interpreter
    """
    def __init__(self, all_vars=None):
        self._namespaces = {
            'uiNamespace': Namespace(),
            'parsingNamespace': Namespace(),
            'missionNamespace': Namespace(all_vars),
            'profileNamespace': Namespace()
        }

        self._current_namespace = self._namespaces['missionNamespace']

    def exception(self, exception):
        """
        We can overwrite this method to handle exceptions differently
        """
        raise exception

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

    def value(self, token, namespace_name=None):
        if isinstance(token, Statement):
            return self.value(self.execute_single(statement=token))
        elif isinstance(token, Variable):
            scope = self.get_scope(token.name, namespace_name)
            return scope[token.name]
        elif isinstance(token, (ConstantValue, Array, Number, Code, Keyword, InterpreterType)):
            return token
        else:
            raise NotImplementedError(repr(token))

    def get_variable(self, token):
        if isinstance(token, Statement):
            return token.base_tokens[0]
        else:
            if not isinstance(token, Variable):
                self.exception(SQFSyntaxError(token.position, 'This must be a variable'))
            return token

    def execute_token(self, token):
        """
        Given a single token, recursively evaluate it and return its value.
        """
        raise NotImplementedError

    def get_scope(self, name, namespace_name=None):
        if namespace_name is None:
            namespace = self._current_namespace
        else:
            namespace = self._namespaces[namespace_name]
        return namespace.get_scope(name)

    def add_scope(self, values=None):
        self._current_namespace.add_scope(values)

    def del_scope(self):
        self._current_namespace.del_scope()

    def add_privates(self, variables):
        for variable in variables:
            if isinstance(variable, Variable):
                name = variable.name
            else:
                assert(isinstance(variable, String))
                name = variable.value

            if not name.startswith('_'):
                self.exception(SQFSyntaxError(variable.position, 'Cannot make global variable "%s" private (underscore missing?)' % name))
            self.current_scope[name] = Nothing

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
            outcome = self.execute_single(statement)
        self.del_scope()
        return outcome

    def execute_single(self, statement):
        """
        Executes a statement
        """
        raise NotImplementedError

    def execute(self, statements):
        """
        Executes a list of statements
        """
        outcome = Nothing
        for statement in statements:
            outcome = self.execute_single(statement)
        return outcome
