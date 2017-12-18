"""
This script is used to write `sqf/dababase.py`, that contains all valid SQF expressions.
It reads a file from here:

https://raw.githubusercontent.com/intercept/intercept/master/src/client/headers/client/sqf_pointers_declaration.hpp

Note that operators with symbols aren't present in this file (!=, ==, ^, etc.) and will need to have their entries restored after running
"""
import urllib.request, urllib.error

from sqf.interpreter_types import ForType, IfType, SwitchType, WhileType, TryType, WithType
from sqf.types import Code, Array, Boolean, Number, Type, Nothing, Anything, String, Namespace, \
    Object, Config, Script, Control, Group, Display, Side, Task, Location, NetObject, DiaryReport, TeamMember


# The mapping of SQF types to our types
STRING_TO_TYPE = {
    'array': Array,
    'scalar': Number,
    'bool': Boolean,
    'code': Code,
    'string': String,
    'text': String,
    'namespace': Namespace,
    'config': Config,
    'location': Location,
    'object': Object,
    'group': Group,
    'member': TeamMember, # team_member gets split
    'control': Control,
    'display': Display,
    'exception': TryType,
    'for': ForType,
    'if': IfType,
    'switch': SwitchType,
    'while': WhileType,
    'with': WithType,
    'side': Side,
    'task': Task,
    'script': Script,
    'nan': Number,
    'nothing': Nothing,
    'netobject': NetObject,
    'any': Type,
    'diary': DiaryReport # diary_record gets split
}

# the argument the type is initialized with
TYPE_TO_INIT_ARGS = {
    Namespace: "'missionNamespace'",
}

# The return type "ANY" means that we do not know it, so it is Nothing()
STRING_TO_TYPE_RETURN = STRING_TO_TYPE.copy()
STRING_TO_TYPE_RETURN['any'] = Anything

WRONG_RETURN_TYPES = {
    'attachedto': Object,
    'getclientstatenumber': Number,
    'handgunmagazine': Array
}

def _parse_type_names(type_names):
    # Alternative types seperated by _ char
    types_names = type_names.split('_')

    # Never care about NaN type (covered by scalar)
    if 'nan' in types_names:
        types_names.remove('nan')

    # Remove parts of types that also get split
    if 'team' in types_names:
        types_names.remove('team')
    if 'record' in types_names:
        types_names.remove('record')

    return types_names

def _parse_return_type_names(return_type_names):
    return_type_names = _parse_type_names(return_type_names)

    if len(return_type_names) > 1 and 'nothing' in return_type_names:
        return_type_names.remove('nothing')

    if len(return_type_names) > 1:
        return_type_name = 'any'
    else:
        return_type_name = return_type_names[0]

    return STRING_TO_TYPE_RETURN[return_type_name]


url = 'https://raw.githubusercontent.com/intercept/intercept/master/src/client/headers/client/sqf_pointers_declaration.hpp'
try:
    data = urllib.request.urlopen(url).read().decode('utf-8').split('\n')
except urllib.error.URLError as e:
    print(e.reason)
    exit()


expressions = []
for line in data:
    if not line.startswith('static '):
        continue

    sections = line.split('__')
    num_sections = len(sections)

    if num_sections not in [4,5,6]:
        print('Couldn''t read function: ', op_name)
        continue

    # Name always comes first
    op_name = sections[1]

    # Return type always comes last (some operators have incorrect values for whatever reason)
    if op_name in WRONG_RETURN_TYPES:
        return_type = WRONG_RETURN_TYPES[op_name]
    else:
        return_type = _parse_return_type_names(sections[num_sections-1][:-1])

    # Adds any relevant initalization argument for the return type
    init_code = ''

    # Number of sections allows us to classify the operation
    if num_sections == 6:
        if return_type in TYPE_TO_INIT_ARGS:
            init_code = ', action=lambda lhs, rhs, i: %s' % TYPE_TO_INIT_ARGS[return_type]

        for lhs_type_name in _parse_type_names(sections[2]):
            lhs_type = STRING_TO_TYPE[lhs_type_name]
            for rhs_type_name in _parse_type_names(sections[3]):
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
    elif num_sections == 5:
        if return_type in TYPE_TO_INIT_ARGS:
            init_code = ', action=lambda rhs, i: %s' % TYPE_TO_INIT_ARGS[return_type]

        for rhs_type_name in _parse_type_names(sections[2]):
            rhs_type = STRING_TO_TYPE[rhs_type_name]
            expression = 'UnaryExpression(' \
                         'Keyword(\'{keyword}\'), ' \
                         '{rhs_type}, {return_type}{init_code})'.format(
                keyword=op_name,
                rhs_type=rhs_type.__name__,
                return_type=return_type.__name__,
                init_code=init_code
            )
            expressions.append(expression)
    else:
        if return_type in TYPE_TO_INIT_ARGS:
            init_code = ', action=lambda i: %s' % TYPE_TO_INIT_ARGS[return_type]

        expression = 'NullExpression(' \
                     'Keyword(\'{keyword}\'), ' \
                     '{return_type}{init_code})'.format(
                keyword=op_name,
                return_type=return_type.__name__,
                init_code=init_code
            )
        expressions.append(expression)

preamble = r'''# This file is generated automatically by `build_database.py`. Change it there.
from sqf.expressions import BinaryExpression, UnaryExpression, NullExpression
from sqf.types import Keyword, Type, Nothing, Anything, String, Code, Array, Number, Boolean, Namespace, \
    Object, Config, Script, Control, Group, Display, Side, Task, Location, NetObject, DiaryReport, TeamMember
from sqf.interpreter_types import WhileType, \
    ForType, SwitchType, IfType, TryType, WithType'''


with open('sqf/database.py', 'w') as f:
    f.write(preamble + '\n\n\n')
    f.write('EXPRESSIONS = [\n    ')
    f.write(',\n    '.join(expressions))
    f.write('\n]\n')
