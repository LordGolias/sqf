from sqf.base_type import BaseType


class Keyword(BaseType):
    def __init__(self, token):
        super().__init__()
        self._token = token
        self._unique_token = token.lower()

    @property
    def value(self):
        return self._token

    def __str__(self):
        return self._token

    def __repr__(self):
        return 'K<%s>' % self._token

    def __hash__(self):
        return hash(str(self.__class__) + self._unique_token)


class KeywordControl(Keyword):
    def __repr__(self):
        return 'KC<%s>' % self._token


class KeywordConstant(Keyword):
    def __repr__(self):
        return 'Kc<%s>' % self._token


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
    'isEqualTo', '==', '!=', '>', '<', '>=', '<=', '!', 'not', '>>',
    'isNull', 'isNil',
    'units',
    'createMarker', 'getmarkerpos',
    'publicVariable', 'publicVariableServer', 'publicVariableClient',
    'addPublicVariableEventHandler', 'isServer', 'isClient', 'isDedicated',
}

KEYWORDS = KEYWORDS.union({'#define','#include', '\\'})

from sqf.keywords_db import DB, DB_constants, DB_controls

KEYWORDS = KEYWORDS.union(DB)
del DB


class Namespace(Keyword):
    pass


NAMESPACES = set(['missionNamespace','profileNamespace','uiNamespace','parsingNamespace'])
NAMESPACES = set([x.lower() for x in NAMESPACES])

KEYWORDS = set([x.lower() for x in KEYWORDS])


# operators by precedence
ORDERED_OPERATORS = [Keyword(s) for s in ('private', '=', '-', 'count', '>', 'units', 'SPAWN', 'spawn', '&&', '!',
                                          'getVariable')]

KEYWORDS_CONTROLS = set(DB_controls)
KEYWORDS_CONTROLS = set([x.lower() for x in KEYWORDS_CONTROLS])
del DB_controls

KEYWORDS_CONSTANTS = set(DB_constants)
KEYWORDS_CONSTANTS = set([x.lower() for x in KEYWORDS_CONSTANTS])
del DB_constants
