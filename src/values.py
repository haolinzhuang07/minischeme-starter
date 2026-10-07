"""Runtime Scheme values and their printer."""
from dataclasses import dataclass
try:
    from .reader import Symbol, Form
except ImportError:  # Allows `python src/main.py` from the repository root.
    from reader import Symbol, Form


class _Nil:
    def __repr__(self):
        return '()'


NIL = _Nil()


@dataclass(eq=False)
class Pair:
    car: object
    cdr: object


@dataclass
class Builtin:
    name: str
    function: object


@dataclass
class Closure:
    params: list
    body: list
    env: object


def is_proper_list(value):
    seen = set()
    while isinstance(value, Pair):
        if id(value) in seen:
            return False
        seen.add(id(value))
        value = value.cdr
    return value is NIL


def list_to_pair(items, tail=NIL):
    result = tail
    for item in reversed(items):
        result = Pair(item, result)
    return result


def quote_datum(expr):
    if isinstance(expr, Form):
        tail = quote_datum(expr.tail) if expr.tail is not None else NIL
        return list_to_pair([quote_datum(x) for x in expr.items], tail)
    return expr


def scheme_repr(value):
    if value is NIL:
        return '()'
    if value is True:
        return '#t'
    if value is False:
        return '#f'
    if isinstance(value, Symbol):
        return value.name
    if isinstance(value, str):
        escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        return f'"{escaped}"'
    if isinstance(value, Pair):
        parts = []
        current = value
        seen = set()
        while isinstance(current, Pair):
            if id(current) in seen:
                parts.append('. #<cycle>')
                break
            seen.add(id(current))
            parts.append(scheme_repr(current.car))
            current = current.cdr
        if current is NIL:
            return '(' + ' '.join(parts) + ')'
        if parts and parts[-1] == '. #<cycle>':
            return '(' + ' '.join(parts) + ')'
        return '(' + ' '.join(parts) + ' . ' + scheme_repr(current) + ')'
    if isinstance(value, (Builtin, Closure)):
        return '#<procedure>'
    if isinstance(value, float):
        return repr(value)
    return str(value)


def ast_repr(expr):
    if isinstance(expr, Form):
        body = ' '.join(ast_repr(x) for x in expr.items)
        if expr.tail is not None:
            body += ' . ' + ast_repr(expr.tail)
        return '(' + body + ')'
    if isinstance(expr, Symbol):
        return expr.name
    if isinstance(expr, str):
        return scheme_repr(expr)
    if expr is True:
        return '#t'
    if expr is False:
        return '#f'
    return str(expr)
