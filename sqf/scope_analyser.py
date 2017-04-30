from sqf.types import Statement, Code, ConstantValue, Number, Boolean, Nothing, Variable, Array, String
from sqf.interpreter_types import InterpreterType, PrivateType
from sqf.keywords import Keyword
from sqf.exceptions import SQFSyntaxError, SQFWarning
from sqf.base_interpreter import BaseInterpreter


CONSTANT_VALUES = (Code, ConstantValue, Number, Boolean, Keyword, Variable, Array, InterpreterType)


class ScopeAnalyzer(BaseInterpreter):
    """
    Analyzer that detects private variables, etc.
    """
    def __init__(self, all_vars=None):
        super().__init__(all_vars)
        self.exceptions = []
        self.privates = []

    def exception(self, exception):
        self.exceptions.append(exception)

    def value(self, token, namespace_name=None):
        if isinstance(token, Variable):
            scope = self.get_scope(token.name, namespace_name)
            if self.current_scope != scope and token.name.startswith('_'):
                self.exception(SQFWarning(token.position, 'Local variable "%s" is not from this scope (not private)' % token))

            return scope[token.name]
        elif isinstance(token, CONSTANT_VALUES):
            return token

    def execute_token(self, token):
        """
        Given a single token, recursively evaluate it and return its value.
        """
        # interpret the statement recursively
        if isinstance(token, Statement):
            result = self.execute_single(statement=token)
        elif isinstance(token, Array):
            result = Array([self.execute_token(s) for s in token.value if s])
        else:
            result = token

        return result

    def _add_params(self, tokens):
        assert(len(tokens) == 2)
        if isinstance(tokens[1], Array):
            for token in tokens[1]:
                if isinstance(token, String):
                    if token.value == '':
                        continue
                    self.add_privates([token])
                elif isinstance(token, Array):
                    if len(token) in [2, 4]:
                        self.add_privates([token[0]])
                        lhs = token[0].value
                        scope = self.get_scope(lhs)
                        scope[lhs] = token[1]
                    else:
                        self.exception(
                            SQFSyntaxError(tokens[1].position, '`params` array element have 2-4 elements'))
                else:
                    self.exception(SQFSyntaxError(tokens[1].position, '`params` array element must be a string or array'))
        else:
            self.exception(SQFSyntaxError(tokens[1].position, '`params` argument must be an array'))

    def execute_single(self, statement):
        assert(not isinstance(statement, Code))

        outcome = Nothing

        # evaluate the types of all tokens
        base_tokens = statement.base_tokens

        if base_tokens and base_tokens[0] == Keyword('#define'):
            return outcome

        tokens = []

        for token in statement.base_tokens:
            t = self.execute_token(token)
            tokens.append(t)

        if len(tokens) == 2 and tokens[0] == Keyword('params'):
            self._add_params(tokens)
        if len(tokens) == 3 and tokens[1] == Keyword('params'):
            self._add_params(tokens[1:])
        if len(tokens) == 2 and tokens[0] == Keyword('private'):
            if isinstance(tokens[1], String):
                self.add_privates([tokens[1]])
            elif isinstance(tokens[1], Array):
                self.add_privates(tokens[1].value)
            elif isinstance(base_tokens[1], Statement) and isinstance(base_tokens[1].base_tokens[0], Variable):
                var = base_tokens[1].base_tokens[0]
                self.add_privates([String('"' + var.name + '"')])
                outcome = PrivateType(var)
                self.privates.append(PrivateType(var))
            else:
                self.exception(SQFSyntaxError(statement.position, '`private` used incorrectly'))
        # assignment operator
        elif len(tokens) == 3 and tokens[1] == Keyword('='):
            if isinstance(tokens[0], PrivateType):
                lhs = tokens[0].variable
                self.privates.remove(tokens[0])
            else:
                lhs = self.get_variable(base_tokens[0])
            rhs = tokens[2]
            rhs_v = self.value(tokens[2])

            if not isinstance(lhs, Variable):
                self.exception(SQFSyntaxError(statement.position, 'lhs of assignment operator cannot be a literal'))
            else:
                scope = self.get_scope(lhs.name)
                if self.current_scope != scope and lhs.name.startswith('_'):
                    self.exception(SQFWarning(lhs.position, 'Local variable assigned "%s" to an outer scope (not private)' % lhs.name))

                scope[lhs.name] = rhs_v
                outcome = rhs
        # code, variables and values
        elif len(tokens) == 1 and isinstance(tokens[0], CONSTANT_VALUES):
            outcome = tokens[0]
        else:
            # force the tokens to be evaluated so it detects variables not assigned.
            for token in base_tokens:
                self.value(token)

        if statement.ending:
            outcome = Nothing
        return outcome

    def execute(self, statements):
        super().execute(statements)

        if self.privates:
            for private in self.privates:
                self.exception(SQFWarning(private.position, 'private argument must be a string.'))


def interpret(statements, scope_analyzer=None):
    if scope_analyzer is None:
        scope_analyzer = ScopeAnalyzer()
    assert(isinstance(scope_analyzer, ScopeAnalyzer))

    scope_analyzer.add_scope({'_this': Nothing})
    scope_analyzer.execute(statements)

    return scope_analyzer
