import copy

from sqf.expressions import InterpreterExpression, EXPRESSIONS, \
    IfThenExpression, IfThenSpecExpression, IfThenElseExpression, \
    ForFromToDoExpression, ForSpecDoExpression, \
    WhileDoExpression, ForEachExpression, SwitchDoExpression, parse_switch
from sqf.types import Statement, Code, ConstantValue, Number, Boolean, Nothing, Variable, Array, String, Type
from sqf.interpreter_types import PrivateType
from sqf.keywords import Keyword
from sqf.exceptions import SQFSyntaxError, SQFWarning
from sqf.base_interpreter import BaseInterpreter


UNTYPED_EXPRESSIONS = copy.deepcopy(EXPRESSIONS)


# the function that every non-typed expression runs. It just executes every element.
def execute(values, interpreter):
    [interpreter.value(x) for x in values]
    return Nothing

# replace all occurrences of constant types by `Type` so the expressions are matched even when
# the types are unknown
TYPES_TO_REPLACE = (String, ConstantValue, Number, Boolean, Array)
for x in UNTYPED_EXPRESSIONS:
    types_or_values = []
    for ts_or_vs in x.types_or_values:
        if not isinstance(ts_or_vs, (list, tuple)):
            if isinstance(ts_or_vs, type):
                if ts_or_vs in TYPES_TO_REPLACE:
                    types_or_values.append((ts_or_vs, Nothing))
                else:
                    types_or_values.append(ts_or_vs)
            else:
                if isinstance(ts_or_vs, TYPES_TO_REPLACE):
                    types_or_values.append((ts_or_vs, Nothing))
                else:
                    types_or_values.append(ts_or_vs)
        else:
            list_ = []
            for t_or_v in ts_or_vs:
                if isinstance(t_or_v, type):
                    list_.append(Type)
                else:  # is a value
                    list_.append(t_or_v)
            types_or_values.append(list_)
    x.types_or_values = types_or_values
    if not isinstance(x, InterpreterExpression) and type(x) != ForEachExpression:
        x.execute = execute


# This allows to first get the typed expressions, and only then try the unknown expressions.
EXPRESSIONS = EXPRESSIONS + UNTYPED_EXPRESSIONS


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
        """
        Given a single token, recursively evaluates and returns its value
        """
        if isinstance(token, Statement):
            return self.value(self.execute_single(statement=token))
        if isinstance(token, Variable):
            scope = self.get_scope(token.name, namespace_name)
            if scope.level == 0 and not token.is_global:
                self.exception(SQFWarning(token.position, 'Local variable "%s" is not from this scope (not private)' % token))

            return scope[token.name]
        elif isinstance(token, Array):
            return Array([self.value(s) for s in token.value])
        else:
            return token

    def execute_token(self, token):
        """
        Given a single token, recursively evaluate it without returning its value (only type)
        """
        # interpret the statement recursively
        if isinstance(token, Statement):
            result = self.execute_single(statement=token)
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
                    if len(token) in (2, 3, 4):
                        self.add_privates([token[0]])
                        lhs = token[0].value
                        scope = self.get_scope(lhs)
                        scope[lhs] = token[1]
                    else:
                        self.exception(
                            SQFSyntaxError(tokens[1].position, '`params` array element must have 2-4 elements'))
                else:
                    self.exception(SQFSyntaxError(tokens[1].position, '`params` array element must be a string or array'))
        else:
            self.exception(SQFSyntaxError(tokens[1].position, '`params` argument must be an array'))

    def execute_single(self, statement):
        assert(isinstance(statement, Statement))

        outcome = Nothing

        base_tokens = statement.base_tokens

        # operations that cannot evaluate the value of all base_tokens
        if base_tokens and base_tokens[0] == Keyword('#define'):
            return outcome
        elif len(base_tokens) == 2 and base_tokens[0] == Keyword('private'):
            # the rhs may be a variable, so we cannot get the value
            rhs = self.execute_token(base_tokens[1])
            if isinstance(rhs, String):
                self.add_privates([rhs])
            elif isinstance(rhs, Array):
                self.add_privates(self.value(rhs))
            elif isinstance(rhs, Variable):
                self.add_privates([String('"' + rhs.name + '"')])
                outcome = PrivateType(rhs)
                self.privates.append(PrivateType(rhs))
            else:
                self.exception(SQFSyntaxError(statement.position, '`private` used incorrectly'))
            return outcome
        # assignment operator
        elif len(base_tokens) == 3 and base_tokens[1] == Keyword('='):
            lhs = self.execute_token(base_tokens[0])
            if isinstance(lhs, PrivateType):
                self.privates.remove(lhs)
                lhs = lhs.variable
            else:
                lhs = self.get_variable(base_tokens[0])

            rhs_v = self.value(base_tokens[2])

            if not isinstance(lhs, Variable):
                self.exception(SQFSyntaxError(statement.position, 'lhs of assignment operator cannot be a literal'))
            else:
                scope = self.get_scope(lhs.name)
                if scope.level == 0 and not lhs.is_global:
                    self.exception(SQFWarning(lhs.position,
                                              'Local variable "%s" assigned to an outer scope (not private)' % lhs.name))

                scope[lhs.name] = rhs_v
                outcome = rhs_v
            if statement.ending:
                outcome = Nothing
            return outcome
        # code, variables and values
        elif len(base_tokens) == 1:
            return self.execute_token(base_tokens[0])

        # evaluate all the base_tokens, trying to obtain their values
        values = []
        for token in base_tokens:
            v = self.value(token)
            values.append(v)

        # try to find a match for any expression, both typed and un-typed
        case_found = None
        for case in EXPRESSIONS:
            if case.is_match(values):
                case_found = case
                break

        if case_found is not None:
            # evaluate the code of an IfThen expression
            if type(case_found) == IfThenExpression:
                self.execute_code(values[2])
            elif type(case_found) == IfThenElseExpression:
                self.execute_code(values[2].then)
                self.execute_code(values[2].else_)
            elif type(case_found) == IfThenSpecExpression:
                self.execute_code(values[2].value[0])
                self.execute_code(values[2].value[1])
            elif type(case_found) == ForFromToDoExpression:
                outcome = self.execute_code(values[2], extra_scope={values[0].variable.value: Number(0)})
            elif type(case_found) == ForSpecDoExpression:
                for code in [values[0].array[0], values[0].array[1], values[0].array[2], values[2]]:
                    outcome = self.execute_code(code)
            elif type(case_found) == WhileDoExpression:
                outcome = self.execute_code(values[2])
            elif type(case_found) == ForEachExpression:
                # let us execute it for a single element. That element is either the first element
                # of the list, or Nothing
                if isinstance(values[2], Array) and len(values[2].value) != 0:
                    element = values[2].value[0]
                else:
                    element = Nothing
                outcome = case_found.execute([values[0], values[1], Array([element])], self)
            elif type(case_found) == SwitchDoExpression:
                conditions = parse_switch(self, values[2])
                for condition, outcome in conditions:
                    if condition != 'default':
                        self.value(condition)
                    if outcome is not None and isinstance(outcome, Code):
                        self.execute_code(outcome)
                outcome = Nothing
            else:
                try:
                    outcome = case_found.execute(values, self)
                except Exception:
                    pass
        elif len(values) == 2 and values[0] == Keyword('params'):
            self._add_params(values)
        elif len(values) == 3 and values[1] == Keyword('params'):
            self._add_params(values[1:])

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
