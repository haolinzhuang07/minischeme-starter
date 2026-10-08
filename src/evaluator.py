"""Evaluator and standard procedures for mini-Scheme."""
import math
import operator
from functools import reduce

try:
    from .reader import Form, Symbol
    from .environment import Environment
    from .values import (NIL, Pair, Builtin, Closure, quote_datum, list_to_pair,
                         is_proper_list, scheme_repr)
except ImportError:  # Allows direct execution of src/main.py.
    from reader import Form, Symbol
    from environment import Environment
    from values import (NIL, Pair, Builtin, Closure, quote_datum, list_to_pair,
                       is_proper_list, scheme_repr)


def _require_count(name, args, minimum=None, maximum=None):
    n = len(args)
    if minimum is not None and n < minimum or maximum is not None and n > maximum:
        expected = str(minimum) if minimum == maximum else f'{minimum} or more' if maximum is None else f'{minimum} to {maximum}'
        raise TypeError(f'{name}: expected {expected} arguments, got {n}')


def _number(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise TypeError(f'expected number, got {scheme_repr(x)}')
    return x


def _trunc_div(a, b):
    if b == 0:
        raise ZeroDivisionError('division by zero')
    quotient = abs(a) // abs(b)
    return -quotient if (a < 0) != (b < 0) else quotient


def _plus(*xs):
    return sum((_number(x) for x in xs), 0)


def _minus(*xs):
    _require_count('-', xs, 1)
    vals = [_number(x) for x in xs]
    return -vals[0] if len(vals) == 1 else reduce(operator.sub, vals[1:], vals[0])


def _multiply(*xs):
    return reduce(operator.mul, (_number(x) for x in xs), 1)


def _divide(*xs):
    _require_count('/', xs, 1)
    vals = [_number(x) for x in xs]
    if len(vals) == 1:
        if vals[0] == 0:
            raise ZeroDivisionError('division by zero')
        return 1 / vals[0]
    result = vals[0]
    for x in vals[1:]:
        if isinstance(result, int) and not isinstance(result, bool) and isinstance(x, int) and not isinstance(x, bool):
            result = _trunc_div(result, x)
        else:
            if x == 0:
                raise ZeroDivisionError('division by zero')
            result /= x
    return result


def _chain_compare(name, fn, args):
    _require_count(name, args, 2)
    for a, b in zip(args, args[1:]):
        numeric_pair = (isinstance(a, (int, float)) and not isinstance(a, bool)
                        and isinstance(b, (int, float)) and not isinstance(b, bool))
        symbol_pair = isinstance(a, Symbol) and isinstance(b, Symbol)
        if not (numeric_pair or symbol_pair):
            raise TypeError(f'{name}: expected numbers or symbols')
        if symbol_pair:
            # Symbols compare by their case-sensitive names.
            a, b = a.name, b.name
        if not fn(a, b):
            return False
    return True


def _list_items(value, name):
    if not is_proper_list(value):
        raise TypeError(f'{name}: expected a proper list')
    result = []
    while isinstance(value, Pair):
        result.append(value.car)
        value = value.cdr
    return result


def _equal(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, Pair):
        return _equal(a.car, b.car) and _equal(a.cdr, b.cdr)
    if a is NIL or isinstance(a, (Builtin, Closure)):
        return a is b
    return a == b


def make_global_env():
    env = Environment()
    funcs = {
        '+': _plus, '-': _minus, '*': _multiply, '/': _divide,
        'modulo': lambda a, b: _number(a) % _number(b),
        'quotient': lambda a, b: _trunc_div(_number(a), _number(b)),
        'expt': lambda a, b: _number(a) ** _number(b),
        'abs': lambda a: abs(_number(a)),
        '=': lambda *xs: _chain_compare('=', operator.eq, xs),
        '<': lambda *xs: _chain_compare('<', operator.lt, xs),
        '>': lambda *xs: _chain_compare('>', operator.gt, xs),
        '<=': lambda *xs: _chain_compare('<=', operator.le, xs),
        '>=': lambda *xs: _chain_compare('>=', operator.ge, xs),
        'not': lambda x: x is False,
        'cons': lambda a, b: Pair(a, b),
        'car': lambda x: x.car if isinstance(x, Pair) else (_raise('car: expected a pair')),
        'cdr': lambda x: x.cdr if isinstance(x, Pair) else (_raise('cdr: expected a pair')),
        'list': lambda *xs: list_to_pair(xs),
        'length': lambda x: len(_list_items(x, 'length')),
        'append': _append,
        'null?': lambda x: x is NIL,
        'pair?': lambda x: isinstance(x, Pair),
        'list?': is_proper_list,
        'number?': lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
        'boolean?': lambda x: type(x) is bool,
        'symbol?': lambda x: isinstance(x, Symbol),
        'string?': lambda x: isinstance(x, str) and not isinstance(x, Symbol),
        'procedure?': lambda x: isinstance(x, (Builtin, Closure)),
        'zero?': lambda x: _number(x) == 0,
        'even?': lambda x: _integer_parity(x, 0),
        'odd?': lambda x: _integer_parity(x, 1),
        'eq?': _eq,
        'equal?': _equal,
        'display': _display,
        'newline': _newline,
    }
    for name, fn in funcs.items():
        env.define(name, Builtin(name, fn))
    return env


def _raise(message):
    raise TypeError(message)


def _integer_parity(value, remainder):
    number = _number(value)
    if not isinstance(number, int):
        raise TypeError('expected integer')
    return number % 2 == remainder


def _append(*lists):
    if not lists:
        return NIL
    result = lists[-1]
    for value in reversed(lists[:-1]):
        items = _list_items(value, 'append')
        result = list_to_pair(items, result)
    return result


def _eq(a, b):
    if isinstance(a, (int, float, bool, Symbol)) and not (isinstance(a, bool) != isinstance(b, bool)):
        if type(a) is type(b) or isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a == b
    if a is NIL or isinstance(a, (Pair, str, Builtin, Closure)):
        return a is b
    return a is b


def _display(value):
    import sys
    sys.stdout.write(value if isinstance(value, str) and not isinstance(value, Symbol) else scheme_repr(value))
    return None


def _newline():
    import sys
    sys.stdout.write('\n')
    return None


def evaluate(expr, env):
    if isinstance(expr, Symbol):
        return env.lookup(expr)
    if not isinstance(expr, Form):
        return expr
    if expr.tail is not None:
        raise TypeError('cannot evaluate an improper list')
    parts = expr.items
    if not parts:
        return NIL
    head = parts[0]
    name = head.name if isinstance(head, Symbol) else None

    if name == 'quote':
        _require_count('quote', parts[1:], 1, 1)
        return quote_datum(parts[1])
    if name == 'if':
        _require_count('if', parts[1:], 2, 3)
        return evaluate(parts[2], env) if evaluate(parts[1], env) is not False else (evaluate(parts[3], env) if len(parts) == 4 else None)
    if name == 'cond':
        for clause in parts[1:]:
            if not isinstance(clause, Form) or clause.tail is not None or not clause.items:
                raise TypeError('cond: malformed clause')
            test = clause.items[0]
            matched = isinstance(test, Symbol) and test.name == 'else'
            test_value = True if matched else evaluate(test, env)
            if matched or test_value is not False:
                return _sequence(clause.items[1:], env) if len(clause.items) > 1 else test_value
        return None
    if name == 'and':
        result = True
        for part in parts[1:]:
            result = evaluate(part, env)
            if result is False:
                return False
        return result
    if name == 'or':
        for part in parts[1:]:
            result = evaluate(part, env)
            if result is not False:
                return result
        return False
    if name == 'define':
        _require_count('define', parts[1:], 2)
        target = parts[1]
        if isinstance(target, Form):
            if target.tail is not None or not target.items or not isinstance(target.items[0], Symbol):
                raise TypeError('define: malformed function definition')
            proc_name, params = target.items[0], target.items[1:]
            closure = Closure(_check_params(params), parts[2:], env)
            env.define(proc_name, closure)
            return proc_name
        if not isinstance(target, Symbol) or len(parts) != 3:
            raise TypeError('define: expected a name and expression')
        env.define(target, evaluate(parts[2], env))
        return target
    if name == 'lambda':
        _require_count('lambda', parts[1:], 2)
        params = parts[1]
        if not isinstance(params, Form) or params.tail is not None:
            raise TypeError('lambda: expected fixed parameter list')
        return Closure(_check_params(params.items), parts[2:], env)
    if name == 'let':
        _require_count('let', parts[1:], 2)
        bindings = parts[1]
        if not isinstance(bindings, Form) or bindings.tail is not None:
            raise TypeError('let: malformed bindings')
        names, values = [], []
        for binding in bindings.items:
            if not isinstance(binding, Form) or binding.tail is not None or len(binding.items) != 2 or not isinstance(binding.items[0], Symbol):
                raise TypeError('let: malformed binding')
            names.append(binding.items[0].name)
            values.append(evaluate(binding.items[1], env))
        local = Environment(env)
        for n, v in zip(names, values):
            local.define(n, v)
        return _sequence(parts[2:], local)
    if name == 'begin':
        return _sequence(parts[1:], env)

    proc = evaluate(head, env)
    args = [evaluate(x, env) for x in parts[1:]]
    return apply(proc, args)


def _check_params(params):
    names = []
    for param in params:
        if not isinstance(param, Symbol) or param.name in names:
            raise TypeError('parameters must be unique symbols')
        names.append(param.name)
    return names


def _sequence(expressions, env):
    result = None
    for expression in expressions:
        result = evaluate(expression, env)
    return result


def apply(proc, args):
    if isinstance(proc, Builtin):
        try:
            return proc.function(*args)
        except TypeError as exc:
            if str(exc).startswith(('expected ', 'car:', 'cdr:', 'length:', 'append:', 'procedure?')):
                raise
            raise TypeError(f'{proc.name}: {exc}') from exc
    if isinstance(proc, Closure):
        if len(args) != len(proc.params):
            raise TypeError(f'procedure: expected {len(proc.params)} arguments, got {len(args)}')
        local = Environment(proc.env)
        for name, value in zip(proc.params, args):
            local.define(name, value)
        return _sequence(proc.body, local)
    raise TypeError(f'{scheme_repr(proc)} is not a procedure')

