"""
This script is used to write `sqf/dababase.py`, that contains all valid SQF expressions.
It requires a file `fullFuncDump1.68.json`, that can be downloaded from here:

https://gist.github.com/LordGolias/1289d59b35359fa3714d3666de396ad7
"""
import json

from sqf.interpreter_types import ForType, IfType, SwitchType, WhileType, TryType, WithType
from sqf.types import Code, Array, Boolean, Number, Type, Nothing, String, Namespace, Object, Config, Script


# The mapping of SQF types to our types
STRING_TO_TYPE = {
    'ARRAY': Array,
    'SCALAR': Number,
    'BOOL': Boolean,
    'CODE': Code,
    'STRING': String,
    'TEXT': String,
    'NAMESPACE': Namespace,
    'CONFIG': Config,
    'LOCATION': Object,
    'OBJECT': Object,
    'GROUP': Object,
    'TEAM_MEMBER': Object,
    'CONTROL': Object,
    'DISPLAY': Object,
    'EXCEPTION': TryType,
    'FOR': ForType,
    'IF': IfType,
    'SWITCH': SwitchType,
    'WHILE': WhileType,
    'WITH': WithType,
    'SIDE': Object,
    'TASK': Object,
    'SCRIPT': Script,
    'NaN': Number,
    'NOTHING': Nothing,
    'NetObject': Object,
    'ANY': Type,
    'DIARY_RECORD': Object
}

# the argument the type is initialized with
TYPE_TO_INIT_ARGS = {
    Namespace: "missionNamespace",
}


# The return type "ANY" means that we do not know it, so it is Nothing()
STRING_TO_TYPE_RETURN = STRING_TO_TYPE.copy()
STRING_TO_TYPE_RETURN['ANY'] = Nothing


with open('fullFuncDump1.68.json') as f:
    data = json.load(f)


expressions = []
priorities = {}
for operator in data['operators']:
    op_name = operator
    for case_data_raw in data['operators'][op_name]:
        case_data = case_data_raw['op']

        priorities[op_name] = case_data_raw['priority']

        for return_type_name in case_data['retT']:
            if return_type_name == 'NaN':
                continue
            return_type = STRING_TO_TYPE_RETURN[return_type_name]
            init_code = ''
            if return_type in TYPE_TO_INIT_ARGS:
                init_code = ', action=lambda lhs, rhs, i: %s' % TYPE_TO_INIT_ARGS[return_type]

            for lhs_type_name in case_data['argL']:
                if lhs_type_name == 'NaN':
                    continue
                lhs_type = STRING_TO_TYPE[lhs_type_name]
                for rhs_type_name in case_data['argR']:
                    if rhs_type_name == 'NaN':
                        continue
                    rhs_type = STRING_TO_TYPE[rhs_type_name]
                    expression = 'BinaryExpression(' \
                                 '{lhs_type}, ' \
                                 'Keyword(\'{keyword}\'), ' \
                                 '{rhs_type}, {return_type}{init_code})'.format(
                        lhs_type=lhs_type.__name__,
                        keyword=op_name,
                        rhs_type=rhs_type.__name__,
                        return_type=return_type.__name__,
                        init_code=init_code
                    )
                    expressions.append(expression)

unary_expressions = {}
for function in data['functions']:
    op_name = function
    for case_data_raw in data['functions'][op_name]:
        case_data = case_data_raw['op']

        return_type_names = case_data['retT']
        if op_name == 'handgunMagazine':
            return_type_names = ['ARRAY']
        elif op_name == 'attachedTo':
            return_type_names = ['OBJECT']

        for return_type_name in return_type_names:
            if return_type_name == 'NaN':
                continue
            return_type = STRING_TO_TYPE_RETURN[return_type_name]

            init_code = ''
            if return_type in TYPE_TO_INIT_ARGS:
                init_code = ', action=lambda rhs, i: %s' % TYPE_TO_INIT_ARGS[return_type]

            for rhs_type_name in case_data['argT']:
                if rhs_type_name == 'NaN':
                    continue
                rhs_type = STRING_TO_TYPE[rhs_type_name]
                expression = 'UnaryExpression(' \
                             'Keyword(\'{keyword}\'), ' \
                             '{rhs_type}, {return_type}{init_code})'.format(
                    keyword=op_name,
                    rhs_type=rhs_type.__name__,
                    return_type=return_type.__name__,
                    init_code=init_code
                )

                unary_expressions[op_name] = rhs_type, return_type
                expressions.append(expression)

for nullop in data['nulars']:
    op_name = nullop
    case_data = data['nulars'][op_name]['op']

    for return_type_name in case_data['retT']:
        if return_type_name == 'NaN':
            continue
        if op_name == 'getClientStateNumber':
            # getClientStateNumber is a SCALAR, not a STRING
            return_type_name = 'SCALAR'
        return_type = STRING_TO_TYPE_RETURN[return_type_name]
        init_code = ''
        if return_type in TYPE_TO_INIT_ARGS:
            init_code = ', action=lambda i: %s' % TYPE_TO_INIT_ARGS[return_type]

        expression = 'NullExpression(' \
                     'Keyword(\'{keyword}\'), ' \
                     '{return_type}{init_code})'.format(
            keyword=op_name, return_type=return_type.__name__, init_code=init_code)
        expressions.append(expression)


preamble = r'''# This file is generated automatically by `build_database.py`. Change it there.
from sqf.expressions import BinaryExpression, UnaryExpression, NullExpression
from sqf.types import Keyword, Type, Nothing, String, Code, Array, Number, Boolean, Namespace, Object, Config, Script
from sqf.interpreter_types import WhileType, \
    ForType, SwitchType, IfType, TryType, WithType'''


with open('sqf/database.py', 'w') as f:
    f.write(preamble + '\n\n\n')
    f.write('EXPRESSIONS = [\n')
    for exp in expressions:
        f.write('    %s,\n' % exp)
    f.write(']\n')
