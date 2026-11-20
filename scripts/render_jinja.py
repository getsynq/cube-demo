#!/usr/bin/env python3
"""Render the Jinja templates in model/ to plain YAML, without a Cube deployment.

Usage: render_jinja.py <output directory>

Cube renders the templates with minijinja and the context of model/globals.py.
This script does the same with the minijinja package for Python. The output is
an approximation of the files that Cube compiles: the security context is empty.
The script copies the YAML files that have no Jinja. It does not copy JavaScript
models, macro files and globals.py.
"""

import importlib.util
import pathlib
import re
import sys
import types

sys.dont_write_bytecode = True

import minijinja

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = ROOT / "model"
JINJA = re.compile(r"{%|{{|{#")


class TemplateContext:
    """The part of cube.TemplateContext that model/globals.py uses."""

    def __init__(self):
        self.functions = {}
        self.filters = {}
        self.variables = {}

    def add_variable(self, name, value):
        self.variables[name] = value

    def add_function(self, name, func):
        self.functions[name] = func

    def add_filter(self, name, func):
        self.filters[name] = func

    def function(self, func):
        return self._register(self.functions, func)

    def filter(self, func):
        return self._register(self.filters, func)

    @staticmethod
    def _register(target, func):
        if callable(func):
            target[func.__name__] = func
            return func

        def decorator(inner):
            target[func] = inner
            return inner

        return decorator


def load_globals():
    sys.modules["cube"] = types.SimpleNamespace(TemplateContext=TemplateContext)
    spec = importlib.util.spec_from_file_location("model_globals", MODEL / "globals.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return next(v for v in vars(module).values() if isinstance(v, TemplateContext))


def main():
    out = pathlib.Path(sys.argv[1])
    context = load_globals()
    env = minijinja.Environment(
        loader=lambda name: (MODEL / name).read_text(),
        # Cube writes a value that is not marked `safe` as a quoted scalar.
        auto_escape_callback=lambda name: "json",
        filters=context.filters,
        globals=context.functions,
    )
    variables = dict(context.variables, COMPILE_CONTEXT={"securityContext": {}})

    for path in sorted(MODEL.rglob("*")):
        if path.suffix not in (".yml", ".yaml"):
            continue
        relative = path.relative_to(MODEL)
        text = path.read_text()
        if JINJA.search(text):
            text = env.render_template(str(relative), **variables)
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        print(f"wrote {relative}")


if __name__ == "__main__":
    main()
