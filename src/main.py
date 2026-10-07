"""Command-line entry point for mini-Scheme."""
import sys

try:
    from .reader import read_all
    from .evaluator import evaluate, make_global_env
    from .values import scheme_repr
except ImportError:  # Supports the required `python src/main.py` command.
    from reader import read_all
    from evaluator import evaluate, make_global_env
    from values import scheme_repr


def run_source(source, env):
    for expression in read_all(source):
        value = evaluate(expression, env)
        if value is not None:
            print(scheme_repr(value))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    env = make_global_env()
    try:
        if argv:
            for filename in argv:
                with open(filename, 'r', encoding='utf-8') as stream:
                    run_source(stream.read(), env)
        else:
            run_source(sys.stdin.read(), env)
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
