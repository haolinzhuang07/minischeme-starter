"""Lexically scoped variable environments."""
try:
    from .reader import Symbol
except ImportError:
    from reader import Symbol


class Environment:
    def __init__(self, parent=None):
        self.bindings = {}
        self.parent = parent

    def define(self, name, value):
        self.bindings[name.name if isinstance(name, Symbol) else name] = value
        return value

    def lookup(self, name):
        key = name.name if isinstance(name, Symbol) else name
        env = self
        while env is not None:
            if key in env.bindings:
                return env.bindings[key]
            env = env.parent
        raise NameError(f'undefined name: {key}')
