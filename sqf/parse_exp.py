
def _normalize(item):
    return str(item).lower()


def partition(exp, ops):
    """
    Splits `exp` by the last occurrence of `op` in a list of 3 elements.
    """
    # one is always found because of the condition used in parse_exp
    if len(ops) == 1:
        index = next(reversed(list(index for index, value in enumerate(exp) if _normalize(value) in ops)))
    else:
        index = next(index for index, value in enumerate(exp) if _normalize(value) in ops)
    return [exp[:index], exp[index], exp[index+1:]]


def parse_exp(exp, priorities, container=list, add_condition=lambda x: x):
    """
    Recursively splits `exp` by a list of ordered operators. `add_condition` is the condition to
    add the result to the container.
    """
    result = exp
    for priority in sorted(priorities.keys()):
        ops = priorities[priority]
        common_ops = set(_normalize(op) for op in exp if _normalize(op) in ops)
        if common_ops and len(exp) > 1:
            result = []
            for i in partition(exp, common_ops):
                if isinstance(i, list):
                    sub_result = parse_exp(i, priorities, container, add_condition)
                    if add_condition(sub_result):  # only put in result non-empty stuff
                        result.append(sub_result)
                else:
                    result.append(i)
            break

    if len(result) == 1:
        return result[0]
    elif isinstance(result, container):
        return result
    else:
        return container(result)
