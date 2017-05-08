from sqf.interpreter_expressions import \
    IfThenExpression, IfThenSpecExpression, IfThenElseExpression, IfThenExitWithExpression, \
    ForFromToDoExpression, ForSpecDoExpression, \
    WhileDoExpression, ForEachExpression, SwitchDoExpression, parse_switch
from sqf.types import Statement, Code, Number, Nothing, Variable, Array, String, Type, File, BaseType
from sqf.interpreter_types import InterpreterType, PrivateType
from sqf.keywords import Keyword
from sqf.expressions import UnaryExpression, BinaryExpression
from sqf.exceptions import SQFParserError, SQFWarning
from sqf.base_interpreter import BaseInterpreter
from sqf.database import EXPRESSIONS
from sqf.expressions_cache import values_to_expressions, build_database


import sqf.interpreter_expressions

## Replace all expressions in `database` by expressions from `expressions` with the same signature
for exp in sqf.interpreter_expressions.EXPRESSIONS:
    if exp in EXPRESSIONS:
        EXPRESSIONS.remove(exp)
    EXPRESSIONS.append(exp)


EXPRESSIONS_MAP = build_database(EXPRESSIONS)


class Analyzer(BaseInterpreter):
    """
    The Analyzer. This is sesentially an interpreter that
    * runs SQF statements that accepts unknown types
    * Stores exceptions instead of rising them.
    * Runs code that is declared but not called.
    """
    def __init__(self, all_vars=None):
        super().__init__(all_vars)
        self.exceptions = []

        # These two are markers indicating that the code was
        self.privates = []
        self._unexecuted_codes = []
        self._executed_codes = []
        self.defines = {}

    def exception(self, exception):
        self.exceptions.append(exception)

    def value(self, token, namespace_name=None):
        """
        Given a single token, recursively evaluates and returns its value
        """
        assert(isinstance(token, BaseType))
        if isinstance(token, Statement):
            result = self.value(self.execute_token(token))
        elif isinstance(token, Variable):
            scope = self.get_scope(token.name, namespace_name)
            if scope.level == 0 and not token.is_global:
                self.exception(SQFWarning(token.position, 'Local variable "%s" is not from this scope (not private)' % token))

            result = scope[token.name]
            result.position = token.position
        elif isinstance(token, Array) and token.value is not None:
            result = Array([self.value(self.execute_token(s)) for s in token.value])
            result.position = token.position
        else:
            null_expressions = values_to_expressions([token], EXPRESSIONS_MAP, EXPRESSIONS)
            if null_expressions:
                result = null_expressions[0].execute([token], self)
            else:
                result = token
            result.position = token.position

        if isinstance(token, Code) and token not in self._unexecuted_codes:
            self._unexecuted_codes.append(token)

        return result

    def execute_token(self, token):
        """
        Given a single token, recursively evaluate it without returning its value (only type)
        """
        # interpret the statement recursively
        if isinstance(token, Statement):
            result = self.execute_single(statement=token)
            # we do not want the position of the statement, but of the token, so we do not
            # store it here
        elif isinstance(token, Array) and token.value is not None:
            result = Array([self.execute_token(s) for s in token.value])
            result.position = token.position
        elif str(token) in self.defines:
            result = self.execute_token(self.defines[str(token)])
            result.position = token.position
        else:
            result = token
            result.position = token.position

        return result

    def execute_unexecuted_code(self, code):
        """
        Executes a code in a dedicated env and put consequence exceptions in self.
        """
        assert (code in self._unexecuted_codes)
        assert (code not in self._executed_codes)
        analyser = Analyzer()
        analyser._executed_codes = self._executed_codes

        file = File(code._tokens)
        file.position = code.position

        analyser.execute_code(file)

        self._executed_codes.extend(analyser._executed_codes)
        self.exceptions.extend(analyser.exceptions)

    def execute_code(self, code, params=None, extra_scope=None):
        if code in self._unexecuted_codes:
            self._unexecuted_codes.remove(code)
        if code in self._executed_codes:  # execute once only to avoid infinite recursions
            result = Nothing()
            result.position = code.position
            return result
        self._executed_codes.append(code)

        outcome = super().execute_code(code, params, extra_scope)

        # collect `private` statements that have a variable but were not collected by the assignment operator
        if isinstance(code, File):
            for code in self._unexecuted_codes[:]:
                self.execute_unexecuted_code(code)
            if self.privates:
                for private in self.privates:
                    self.exception(SQFWarning(private.position, 'private argument must be a string.'))

        return outcome

    def execute_single(self, statement):
        assert(isinstance(statement, Statement))

        outcome = Nothing()
        outcome.position = statement.position

        base_tokens = statement.base_tokens
        if not base_tokens:
            return outcome

        # operations that cannot evaluate the value of all base_tokens
        if base_tokens[0] in (Keyword('#ifdef'), Keyword('#endif')):
            return outcome
        if base_tokens[0] == Keyword('#define'):
            if len(base_tokens) < 2:
                exception = SQFParserError(base_tokens[0].position, "#define must have at least one argument")
                self.exception(exception)
            elif len(base_tokens) == 2: # e.g. #define a 2
                value = Nothing()
                value.position = base_tokens[1].position
                self.defines[str(base_tokens[1])] = value
            elif len(base_tokens) == 3:  # e.g. #define a(_x) (_x)
                self.defines[str(base_tokens[1])] = base_tokens[2]
            else:  # e.g. #define a(_x) b(_x)
                define_statement = Statement(statement.base_tokens[3:])
                define_statement.position = base_tokens[3].position
                self.defines[str(base_tokens[1])] = define_statement
            return outcome
        elif base_tokens[0] == Keyword("#include"):
            if len(base_tokens) != 2 or type(base_tokens[1]) != String:
                exception = SQFParserError(base_tokens[0].position, "Wrong syntax for #include")
                self.exception(exception)
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
                outcome.position = rhs.position
                self.privates.append(outcome)
            else:
                self.exception(SQFParserError(base_tokens[0].position, '`private` used incorrectly'))
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
                self.exception(SQFParserError(base_tokens[0].position, 'lhs of assignment operator must be a variable'))
            else:
                scope = self.get_scope(lhs.name)
                scope[lhs.name] = rhs_v

                if scope.level == 0 and not lhs.is_global:
                    self.exception(
                        SQFWarning(lhs.position, 'Local variable "%s" assigned to an outer scope (not private)' % lhs.name))

                if not statement.ending:
                    outcome = rhs_v
            return outcome
        # A variable can only be evaluated if we need its value, so we will not call its value until the very end.
        elif len(base_tokens) == 1 and type(base_tokens[0]) in (Variable, Array):
            return self.execute_token(base_tokens[0])
        # heuristic for defines (that are thus syntactically correct):
        #   - global variable followed by a parenthesis statement
        #   - first token is a define
        elif len(base_tokens) == 2 and (
                            type(base_tokens[0]) == Variable and base_tokens[0].is_global or
                            str(base_tokens[0]) in self.defines) and \
                type(base_tokens[1]) == Statement and base_tokens[1].parenthesis:
            return outcome

        # evaluate all the base_tokens, trying to obtain their values
        values = []
        tokens = []
        for token in base_tokens:
            t = self.execute_token(token)
            v = self.value(t)
            tokens.append(t)
            values.append(v)

        # try to find a match for any expression, both typed and un-typed
        case_found = None
        possible_expressions = values_to_expressions(values, EXPRESSIONS_MAP, EXPRESSIONS)
        for case in possible_expressions:
            if case.is_signature_match(values):  # match first occurrence
                case_found = case
                break

        if case_found:
            # evaluate the code of an IfThen expression
            if type(case_found) == IfThenExpression:
                outcome = self.execute_code(values[2])
            elif type(case_found) == IfThenElseExpression:
                outcome = self.execute_code(values[2].then)
                self.execute_code(values[2].else_)
            elif type(case_found) == IfThenSpecExpression:
                self.execute_code(values[2].value[0])
                outcome = self.execute_code(values[2].value[1])
            elif type(case_found) == IfThenExitWithExpression:
                outcome = self.execute_code(values[2])
            elif type(case_found) == ForFromToDoExpression:
                outcome = self.execute_code(values[2], extra_scope={values[0].variable.value: Number(0)})
            elif type(case_found) == ForSpecDoExpression:
                if values[0].array is not None:
                    for code in [values[0].array[0], values[0].array[1], values[2], values[0].array[2]]:
                        outcome = self.execute_code(code)
            elif type(case_found) == WhileDoExpression:
                self.execute_code(values[0].condition)
                outcome = self.execute_code(values[2])
            elif type(case_found) == ForEachExpression:
                # let us execute it for a single element. That element is either the first element
                # of the list, or Nothing
                if isinstance(values[2], Array) and values[2].value:
                    element = values[2].value[0]
                else:
                    element = Nothing()
                outcome = case_found.execute([values[0], values[1], Array([element])], self)
            elif type(case_found) == SwitchDoExpression:
                self._executed_codes.append(values[2])
                self._unexecuted_codes.remove(values[2])
                conditions = parse_switch(self, values[2])
                for condition, outcome_statement in conditions:
                    if condition != 'default':
                        self.value(condition)
                    if outcome_statement is not None:
                        outcome_code = self.value(outcome_statement)
                        if isinstance(outcome_code, Code):
                            self.execute_code(outcome_code)
                        elif outcome_code != Nothing():
                            self.exception(SQFWarning(outcome_statement.position, "'case' 4th part must be code"))
            elif type(case_found) == BinaryExpression and \
                    case_found.keyword == Keyword('call') and \
                    not case_found.is_match(values):
                # invalidate type of all arrays (since they are passed by
                # reference and thus can be modified by the call)
                if isinstance(tokens[0], Array) and tokens[0].value is not None:
                    arguments = tokens[0].value
                else:
                    arguments = [tokens[0]]

                for argument in arguments:
                    if isinstance(argument, Variable):
                        scope = self.get_scope(argument.name)
                        replace = Nothing()
                        replace.position = argument.position
                        scope[argument.name] = replace
            elif case_found.keyword == Keyword('count') and isinstance(values[0], Code):
                outcome = self.execute_code(values[0], extra_scope={'_x': Nothing()})
            elif case_found.keyword == Keyword('select') and isinstance(values[2], Code):
                outcome = self.execute_code(values[2], extra_scope={'_x': Nothing()})
            elif case_found.is_match(values) or any(map(lambda x: isinstance(x, InterpreterType), values)):
                # if exact match or partial match on `InterpreterType`, we run them.
                outcome = case_found.execute(values, self)
            elif len(possible_expressions) == 1 and possible_expressions[0].return_type is not None:
                outcome = possible_expressions[0].return_type()
            assert(isinstance(outcome, Type))
        elif len(values) == 1:
            if not isinstance(values[0], Type):
                self.exception(
                    SQFParserError(statement.position, '"%s" is syntactically incorrect (missing ;?)' % statement))
            outcome = values[0]
        elif isinstance(base_tokens[0], Variable) and base_tokens[0].is_global:
            # statements starting with a global are likely defined somewhere else
            # todo: catch globals with statements and without statements
            pass
        elif len(possible_expressions) > 0:
            if isinstance(possible_expressions[0], UnaryExpression):
                types_or_values = []
                for exp in possible_expressions:
                    types_or_values.append(exp.types_or_values[1].__name__)

                keyword_name = possible_expressions[0].types_or_values[0].value

                message = 'Unary operator "%s" only accepts argument of types [%s] (rhs is %s)' % \
                          (keyword_name, ','.join(types_or_values), values[1].__class__.__name__)
            elif isinstance(possible_expressions[0], BinaryExpression):
                types_or_values = []
                for exp in possible_expressions:
                    types_or_values.append('(%s,%s)' % (exp.types_or_values[0].__name__, exp.types_or_values[2].__name__))

                keyword_name = possible_expressions[0].types_or_values[1].value

                message = 'Binary operator "{0}" arguments must be [{1}]'.format(
                    keyword_name, ','.join(types_or_values))
                if values[0].__class__.__name__ not in [x[0] for x in types_or_values]:
                    message += ' (lhs is %s' % values[0].__class__.__name__
                if values[0].__class__.__name__ not in [x[1] for x in types_or_values]:
                    message += ', rhs is %s)' % values[2].__class__.__name__
                else:
                    message += ')'
            else:
                assert False

            self.exception(SQFParserError(tokens[0].position, message))
        else:
            self.exception(
                SQFParserError(tokens[0].position, 'statement is syntactically incorrect (missing ;?)'))

        if statement.ending:
            outcome = Nothing()

        assert(isinstance(outcome, BaseType))
        # the position of Private is different because it can be passed from analyser to analyser,
        # and we want to keep the position of the outermost analyser.
        if not isinstance(outcome, PrivateType):
            outcome.position = statement.position

        return outcome


def analyze(statement, analyzer=None):
    assert (isinstance(statement, Statement))
    if analyzer is None:
        analyzer = Analyzer()

    file = File(statement._tokens)

    file.position = (1, 1)

    arg = Nothing()
    arg.position = (1, 1)

    analyzer.execute_code(file, extra_scope={'_this': arg})

    return analyzer
