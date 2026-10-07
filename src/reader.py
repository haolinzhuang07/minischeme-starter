"""Tokenizer and reader for the mini-Scheme subset."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    name: str

    def __str__(self):
        return self.name


@dataclass
class Form:
    items: list
    tail: object = None


class ReadError(Exception):
    pass


def tokenize(source):
    tokens = []
    i = 0
    while i < len(source):
        ch = source[i]
        if ch.isspace():
            i += 1
        elif ch == ';':
            end = source.find('\n', i)
            i = len(source) if end < 0 else end + 1
        elif ch in "()'":
            tokens.append(ch)
            i += 1
        elif ch == '"':
            i += 1
            chars = []
            while i < len(source) and source[i] != '"':
                if source[i] == '\\':
                    i += 1
                    if i >= len(source):
                        raise ReadError('unterminated string escape')
                    escapes = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}
                    if source[i] not in escapes:
                        raise ReadError(f'unknown string escape: \\{source[i]}')
                    chars.append(escapes[source[i]])
                    i += 1
                else:
                    chars.append(source[i])
                    i += 1
            if i >= len(source):
                raise ReadError('unterminated string')
            i += 1
            tokens.append(('STRING', ''.join(chars)))
        else:
            start = i
            while i < len(source) and not source[i].isspace() and source[i] not in "();'\"":
                i += 1
            tokens.append(source[start:i])
    return tokens


def _atom(token):
    if isinstance(token, tuple) and token[0] == 'STRING':
        return token[1]
    if token == '#t':
        return True
    if token == '#f':
        return False
    try:
        return int(token)
    except (ValueError, TypeError):
        pass
    if isinstance(token, str) and any(c in token for c in '.eE'):
        try:
            return float(token)
        except ValueError:
            pass
    return Symbol(token)


def read_all(source):
    tokens = tokenize(source)
    pos = 0

    def read_one():
        nonlocal pos
        if pos >= len(tokens):
            raise ReadError('unexpected end of input')
        token = tokens[pos]
        pos += 1
        if token == "'":
            return Form([Symbol('quote'), read_one()])
        if token == '(':
            items = []
            tail = None
            while True:
                if pos >= len(tokens):
                    raise ReadError('missing closing parenthesis')
                if tokens[pos] == ')':
                    pos += 1
                    return Form(items, tail)
                if tokens[pos] == '.':
                    if not items or tail is not None:
                        raise ReadError('misplaced dot')
                    pos += 1
                    tail = read_one()
                    if pos >= len(tokens) or tokens[pos] != ')':
                        raise ReadError('dotted pair must have one tail')
                    pos += 1
                    return Form(items, tail)
                items.append(read_one())
        if token == ')':
            raise ReadError('unexpected closing parenthesis')
        return _atom(token)

    expressions = []
    while pos < len(tokens):
        expressions.append(read_one())
    return expressions
