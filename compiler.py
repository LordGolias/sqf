from parser import parse


def compile(script):
    statements = parse(script)

    return _compile(statements)


def _compile(statements):
    pass


if __name__ == '__main__':

    test = '''
    private ["_text","_f"];
    _f = diag_fps;
    _text = format ["Units %1 Groups %2 DeadUnits %3 Vehicles %4 FPS %5 CIVLIANS %6 EAST %7 WEST %8 OBJECTS %9 ENTITES %10",count Allunits, count allgroups, count alldeadmen, count vehicles,diag_fps, {side _x == CIVILIAN} count allunits, {side _x == EAST} count allunits, {side _x == WEST} count allunits,count allMissionObjects "All",count entities "All"];
    hint _text;
'''
    print(len(parse(test)))
    print(str(parse(test)))

