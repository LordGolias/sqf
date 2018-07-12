import re


def tokenize(statement):
    # the len=2 tokens have to be first!
    regex = r'(\#\#|\#include|\#else|\#endif|\#ifndef|\#ifdef|\#define|\\\n|\r\n|>>|\/\*|\*\/|\|\||//|!=|<=|>=|==|\n|\t|[\"\' =:\{\}\(\)\[\];/,\!\/\#\*\%\^\-\+<>])'
    return list(filter(None, re.split(regex, statement)))
