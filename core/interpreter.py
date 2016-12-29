from core.types import Statement, Code, ConstantValue, Number, Boolean, Nothing, Variable, Array, String
from core.operators import Operator, OPERATORS, OP_OPERATIONS, OP_ARITHMETIC, OP_ARRAY_OPERATIONS, OP_COMPARISON
from core.parser import parse
from core.exceptions import WrongTypes


class Scope:

    def __init__(self):
        self.variables_values = {}

    def value(self, token):
        """
        Returns the value of the token taking into account that
        it may be a
        """
        if isinstance(token, Variable):
            if token.name in self.variables_values:
                return self.variables_values[token.name]
            else:
                # undeclared variables return Nothing
                return Nothing
        elif isinstance(token, (ConstantValue, Array, Code)):
            return token
        else:
            raise NotImplementedError(token)

    def type(self, token):
        return type(self.value(token))

    def _interpret_token(self, token):
        """
        Given a single token, recursively evaluate it and return its value.
        """
        # interpret the statement recursively
        if isinstance(token, Statement):
            result = self.interpret_statement(statement=token)
        else:
            result = token

        return result, self.value(result)

    def interpret_statement(self, statement):
        scope = self
        if statement.parenthesis == '{}':
            scope = Scope()

        outcome = Nothing

        tokens = statement.tokens
        if len(tokens) == 3 and isinstance(tokens[1], Operator):
            # it is a binary statement: token, operation, token
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

                rhs, rhs_v = scope._interpret_token(rhs)

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
            elif op == OPERATORS['set']:
                # https://community.bistudio.com/wiki/set
                if lhs_t == rhs_t == Array:
                    index = rhs_v.value[0].value
                    value = rhs_v.value[1]
                    if index >= len(lhs_v.value):
                        scope.variables_values[lhs.name].extend(index)
                    scope.variables_values[lhs.name].set(index, value)
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
        elif len(tokens) == 2 and isinstance(tokens[0], Operator):
            op = tokens[0]
            rhs = tokens[1]

            # a token has its type (lhs), its return value (lhs_v), and its type (lhs_t)
            rhs, rhs_v = scope._interpret_token(rhs)
            rhs_t = type(rhs_v)

            if op == OPERATORS['reverse']:
                # https://community.bistudio.com/wiki/reverse
                if rhs_t == Array:
                    rhs_v.reverse()
                    outcome = Nothing
                else:
                    raise WrongTypes()
        elif len(tokens) == 1 and isinstance(tokens[0], Statement):
            outcome = self.interpret_statement(tokens[0])
        elif len(tokens) == 1 and isinstance(tokens[0], Code):
            outcome = tokens[0]
        else:
            raise NotImplementedError('Interpretation of %s not implemented' % tokens)

        if statement.ending:
            outcome = Nothing
        return outcome


def interpret(script):
    statements = parse(script)

    global_scope = Scope()
    local_scope = Scope()

    for statement in statements:
        outcome = local_scope.interpret_statement(statement)

    return global_scope, local_scope, outcome
