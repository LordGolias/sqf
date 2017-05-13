from sqf.types import Statement, Code, Nothing, Variable, Array, String, Type, File
from sqf.keywords import Keyword
from sqf.exceptions import SQFParserError
import sqf.namespace


class BaseInterpreter:
    """
    Base Interpreter used by the analyzer and interpreter
    """
    def __init__(self, all_vars=None):
        self._namespaces = {
            'uinamespace': sqf.namespace.Namespace('uinamespace'),
            'parsingnamespace': sqf.namespace.Namespace('parsingnamespace'),
            'missionnamespace': sqf.namespace.Namespace('missionnamespace', all_vars),
            'profilenamespace': sqf.namespace.Namespace('profilenamespace')
        }

        self.current_namespace = self.namespace('missionnamespace')

    def exception(self, exception):
        """
        We can overwrite this method to handle exceptions differently
        """
        raise exception

    def set_global_variable(self, var_name, value):
        assert(isinstance(value, Type))
        self.namespace('missionNamespace').base_scope[var_name] = value

    def namespace(self, name):
        return self._namespaces[name.lower()]

    @property
    def current_scope(self):
        return self.current_namespace.current_scope

    def __getitem__(self, name):
        return self.get_scope(name)[name]

    def __contains__(self, name):
        return name in self.get_scope(name)

    def _add_params(self, token):
        self.add_privates([token[0]])

    def add_params(self, base_token):
        assert (isinstance(base_token, Array))
        for token in base_token:
            if isinstance(token, String):
                if token.value == '':
                    continue
                self.add_privates([token])
            elif isinstance(token, Array):
                if len(token) in (2, 3, 4):
                    self._add_params(token)
                else:
                    self.exception(
                        SQFParserError(base_token.position, '`params` array element must have 2-4 elements'))
            else:
                self.exception(SQFParserError(base_token.position, '`params` array element must be a string or array'))

    def value(self, token, namespace_name=None):
        if isinstance(token, Statement):
            return self.value(self.execute_single(statement=token))
        elif isinstance(token, Variable):
            scope = self.get_scope(token.name, namespace_name)
            assert isinstance(scope[token.name], Type)
            return scope[token.name]
        elif isinstance(token, (Type, Keyword)):
            return token
        else:
            raise NotImplementedError(repr(token))

    def get_variable(self, token):
        if isinstance(token, Statement):
            return self.get_variable(token.base_tokens[0])
        else:
            if not isinstance(token, Variable):
                return Nothing()
            return token

    def execute_token(self, token):
        """
        Given a single token, recursively evaluate it and return its value.
        """
        raise NotImplementedError

    def get_scope(self, name, namespace_name=None):
        if namespace_name is None:
            namespace = self.current_namespace
        else:
            namespace = self.namespace(namespace_name)
        return namespace.get_scope(name)

    def add_privates(self, variables):
        for variable in variables:
            assert(isinstance(variable, String))
            name = variable.value

            if not name.startswith('_'):
                self.exception(SQFParserError(variable.position, 'Cannot make global variable "%s" private (underscore missing?)' % name))
            self.current_scope[name] = Nothing()

    def execute_other(self, statement):
        pass

    def execute_code(self, code, params=None, extra_scope=None, namespace_name='missionnamespace'):
        assert (isinstance(code, Code))

        # store the old namespace
        _previous_namespace = self.current_namespace

        # store the executing namespace
        namespace = self.namespace(namespace_name)
        # change to the executing namespace
        self.current_namespace = namespace

        if params is None:
            params = Nothing()
            params.position = code.position
        if extra_scope is None:
            extra_scope = {}
        extra_scope['_this'] = params
        namespace.add_scope(extra_scope)

        # execute the code
        outcome = Nothing()
        outcome.position = code.position
        for statement in code.base_tokens:
            outcome = self.value(self.execute_single(statement))

        # cleanup
        if not isinstance(code, File):  # so we have access to its scope
            # this has to be the executing namespace because "self.current_namespace" may change
            namespace.del_scope()
        self.current_namespace = _previous_namespace
        return outcome

    def execute_single(self, statement):
        """
        Executes a statement
        """
        raise NotImplementedError
