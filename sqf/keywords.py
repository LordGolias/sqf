from sqf.base_type import BaseType


class Keyword(BaseType):
    def __init__(self, token):
        super().__init__()
        self._token = token

    @property
    def value(self):
        return self._token

    def __str__(self):
        return self._token

    def __repr__(self):
        return 'R<%s>' % self._token

    def __hash__(self):
        return hash(self._token)


KEYWORDS = {
    'if', 'then', 'else', 'do', 'while', 'for', 'to', 'from', 'step', 'foreach',
    '(', ')', '[', ']', '{', '}',
    ',', ':', ';', 'nil',
    'case', 'switch', 'default',
    'private',
    '=', '+', '-', '*', '/', '%', 'mod', '^', 'max', 'floor',
    'toArray', 'toString',
    'setVariable', 'getVariable',
    'resize', 'count', 'set', 'in', 'select', 'find', 'append', 'pushBack', 'pushBackUnique', 'reverse',
    'call', 'spawn', 'SPAWN',
    '&&', 'and', '||', 'or',
    'isEqualTo', '==', '!=', '>', '<', '>=', '<=', '!', 'not',
    'isNull', 'isNil',
    'units',
    'createMarker', 'getmarkerpos',
    'publicVariable', 'publicVariableServer', 'publicVariableClient',
    'addPublicVariableEventHandler', 'isServer', 'isClient', 'isDedicated',
}

from sqf.keywords_db import DB

KEYWORDS = KEYWORDS.union(DB)
del DB


class Namespace(Keyword):
    pass


NAMESPACES = [Namespace('missionNamespace'), Namespace('profileNamespace'), Namespace('uiNamespace'),
              Namespace('parsingNamespace')]

KEYWORDS = set(Keyword(s) for s in KEYWORDS)
KEYWORDS = KEYWORDS.union(NAMESPACES)

KEYWORDS_MAPPING = dict()
for keyword in KEYWORDS:
    KEYWORDS_MAPPING[keyword.value] = keyword

# operators by precedence
ORDERED_OPERATORS = [Keyword(s) for s in ('private', '=', '-', 'count', '>', 'units', 'SPAWN', 'spawn', '&&', '!',
                                          'getVariable')]
