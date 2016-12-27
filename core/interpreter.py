from core.types import Number, Boolean, Nothing, Variable, Operator, Array, String, \
    OPERATORS, OP_OPERATIONS, OP_ARITHMETIC, OP_ARRAY_OPERATIONS, OP_COMPARISON
from core.statements import Statement
from parser import parse
from exceptions import WrongTypes


class Scope:

    def __init__(self):
        self.variables_values = {}

    def _return_value(self, result):
        if isinstance(result, Variable):
            if result.name in self.variables_values:
                value = self.variables_values[result.name]
            else:
                # undeclared variables return Nothing
                value = Nothing
        else:
            value = result

        return value

    def _interpret_token(self, token):
        """
        Given a single token, recursively evalute it and return its value.
        """
        # we first interpret the statement recursively
        if isinstance(token, Statement):
            result = self.interpret_statement(statement=token)
        else:
            result = token

        return result, self._return_value(result)

    def interpret_statement(self, statement):

        scope = self
        if statement.parenthesis == '{}':
            scope = Scope()

        outcome = Nothing

        tokens = statement.tokens
        if len(tokens) == 3 and isinstance(tokens[1], Operator):
            # it is a binary statement (token, operation, token)
            lhs = tokens[0]
            op = tokens[1]
            rhs = tokens[2]

            # a token has its type (lhs), its return value (lhs_v), and its type (lhs_t)
            lhs, lhs_v = scope._interpret_token(lhs)
            lhs_t = type(lhs_v)
            rhs, rhs_v = scope._interpret_token(rhs)
            rhs_t = type(rhs_v)

            if op == OPERATORS['=']:
                assert(isinstance(lhs, Variable))

                scope.variables_values[lhs.name] = rhs_v
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
        else:
            # it is a non-binary operator
            raise NotImplementedError

        if statement.ending:
            outcome = Nothing
        return outcome


def interpret(script):
    statements = parse(script)

    global_scope = Scope()
    local_scope = Scope()

    if len(statements) > 1 and all(isinstance(statement, Statement) for statement in statements):
        for statement in statements:
            outcome = local_scope.interpret_statement(statement)
    else:
        outcome = local_scope.interpret_statement(statements)
    return global_scope, local_scope, outcome
