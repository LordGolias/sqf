from core.tokenizer_source.tokenize import tokenize as raw_tokenize


def tokenize(statement):
    statement = statement.replace('\n', ' ').strip()

    tokens = raw_tokenize(statement, ('"', ' ', '=', '==', '{', '}', 'if', 'then', 'else', '(', ')', '[', ']', ';', ',', '!', '!='))

    return [token for token in tokens if token]
