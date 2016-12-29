def partition(exp, op):
    # one is always found because of the condition used in parse_exp
    index = next(index for index, value in enumerate(exp) if value == op)
    return [exp[:index], exp[index], exp[index+1:]]


def parse_exp(exp, operators, container=list):
    result = exp
    for op in operators:
        if op in exp and exp != op:
            result = []
            for i in partition(exp, op):
                if isinstance(i, list):
                    sub_result = parse_exp(i, operators, container)
                    if sub_result:  # only put in result non-empty stuff
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
