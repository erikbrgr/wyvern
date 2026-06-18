"""
Registry of built-in names available in Draconic scripts, including:
- Draconic safe built-ins (subset of Python built-ins)
- Avrae aliasing API functions and objects
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class BuiltinInfo:
    name: str
    kind: Literal["function", "variable", "class", "constant"]
    signature: str
    doc: str
    params: list[str] | None = None
    return_type: str | None = None


def _fn(name: str, sig: str, doc: str, params: list[str] | None = None, ret: str | None = None) -> BuiltinInfo:
    return BuiltinInfo(name, "function", sig, doc, params, ret)


def _cls(name: str, sig: str, doc: str) -> BuiltinInfo:
    return BuiltinInfo(name, "class", sig, doc)


def _var(name: str, sig: str, doc: str) -> BuiltinInfo:
    return BuiltinInfo(name, "variable", sig, doc)


def _const(name: str, doc: str) -> BuiltinInfo:
    return BuiltinInfo(name, "constant", name, doc)


# ---------------------------------------------------------------------------
# Draconic-safe Python built-ins
# Source: avrae/draconic helpers.py and interpreter.py
# ---------------------------------------------------------------------------
_DRACONIC_BUILTINS: list[BuiltinInfo] = [
    _fn("abs", "abs(x)", "Return the absolute value of a number.", ["x"], "int | float"),
    _fn("all", "all(iterable)", "Return True if all elements of the iterable are true.", ["iterable"], "bool"),
    _fn("any", "any(iterable)", "Return True if any element of the iterable is true.", ["iterable"], "bool"),
    _fn("ceil", "ceil(x)", "Return the ceiling of x as an integer.", ["x"], "int"),
    _fn("enumerate", "enumerate(iterable, start=0)", "Return an enumerate object.", ["iterable", "start=0"], "enumerate"),
    _fn("filter", "filter(function, iterable)", "Construct an iterator from elements for which function returns true.", ["function", "iterable"], "filter"),
    _fn("floor", "floor(x)", "Return the floor of x as an integer.", ["x"], "int"),
    _fn("len", "len(s)", "Return the length of an object.", ["s"], "int"),
    _fn("map", "map(function, iterable)", "Return an iterator that applies function to every item of iterable.", ["function", "iterable"], "map"),
    _fn("max", "max(iterable, *, key=None)", "Return the largest item in an iterable.", ["iterable", "key=None"], "Any"),
    _fn("min", "min(iterable, *, key=None)", "Return the smallest item in an iterable.", ["iterable", "key=None"], "Any"),
    _fn("print", "print(*objects, sep=' ', end='\\n')", "Print objects to the output.", ["*objects", "sep=' '", "end='\\n'"], "None"),
    _fn("range", "range(stop) | range(start, stop, step=1)", "Return a range object.", ["start", "stop", "step=1"], "range"),
    _fn("reversed", "reversed(seq)", "Return a reverse iterator.", ["seq"], "reversed"),
    _fn("round", "round(number, ndigits=0)", "Round a number to a given precision.", ["number", "ndigits=0"], "float"),
    _fn("set", "set(iterable=())", "Return a new set object.", ["iterable=()"], "set"),
    _fn("sorted", "sorted(iterable, *, key=None, reverse=False)", "Return a new sorted list.", ["iterable", "key=None", "reverse=False"], "list"),
    _fn("sum", "sum(iterable, start=0)", "Sum the items of an iterable.", ["iterable", "start=0"], "int | float"),
    _fn("typeof", "typeof(x)", "Return the type name of x as a string. (Draconic alternative to type())", ["x"], "str"),
    _fn("zip", "zip(*iterables)", "Make an iterator that aggregates elements from each iterable.", ["*iterables"], "zip"),
    _cls("bool", "bool(x=False)", "Convert a value to Boolean."),
    _cls("dict", "dict(**kwargs)", "Create a new dictionary."),
    _cls("float", "float(x=0.0)", "Convert a value to floating-point."),
    _cls("int", "int(x=0, base=10)", "Convert a value to integer."),
    _cls("list", "list(iterable=())", "Create a new list."),
    _cls("str", "str(object='')", "Convert a value to string."),
    _cls("tuple", "tuple(iterable=())", "Create a new tuple."),
    _const("True", "Boolean true constant."),
    _const("False", "Boolean false constant."),
    _const("None", "The None singleton."),
]

# ---------------------------------------------------------------------------
# Avrae Aliasing API
# Source: https://avrae.readthedocs.io/en/latest/aliasing/api.html
# ---------------------------------------------------------------------------
_AVRAE_BUILTINS: list[BuiltinInfo] = [
    _fn("roll", "roll(dice)", "Roll a dice expression and return the total as an integer.\n\nExamples: `roll('1d20+5')`, `roll('2d6')`", ["dice: str"], "int"),
    _fn("vroll", "vroll(dice, multiply=1, add=0)", "Roll a dice expression verbosely and return a SimpleRollResult object.\n\n`result.total` — the integer result\n`result.dice` — individual dice rolled\n`result.full` — full verbose output string", ["dice: str", "multiply=1", "add=0"], "SimpleRollResult"),
    _fn("load_json", "load_json(jsonstr)", "Parse a JSON string and return the corresponding Python object.", ["jsonstr: str"], "Any"),
    _fn("dump_json", "dump_json(obj)", "Serialize a Python object to a JSON string.", ["obj"], "str"),
    _fn("get_gvar", "get_gvar(address)", "Fetch the value of a global variable (GVAR) by its address UUID.", ["address: str"], "str"),
    _fn("set_uvar", "set_uvar(name, value)", "Set a user variable. Value is stored as a string.", ["name: str", "value: str"], "None"),
    _fn("get_uvar", "get_uvar(name, default=None)", "Get a user variable. Returns default if not set.", ["name: str", "default=None"], "str | None"),
    _fn("delete_uvar", "delete_uvar(name)", "Delete a user variable.", ["name: str"], "None"),
    _fn("set_svar", "set_svar(name, value)", "Set a server variable. Requires Manage Server permission.", ["name: str", "value: str"], "None"),
    _fn("get_svar", "get_svar(name, default=None)", "Get a server variable. Returns default if not set.", ["name: str", "default=None"], "str | None"),
    _fn("delete_svar", "delete_svar(name)", "Delete a server variable.", ["name: str"], "None"),
    _fn("set_cvar", "set_cvar(name, value)", "Set a character variable on the active character.", ["name: str", "value: str"], "None"),
    _fn("get_cvar", "get_cvar(name, default=None)", "Get a character variable from the active character.", ["name: str", "default=None"], "str | None"),
    _fn("delete_cvar", "delete_cvar(name)", "Delete a character variable from the active character.", ["name: str"], "None"),
    _fn("err", "err(msg)", "Raise an error and stop alias execution with the given message.", ["msg: str"], "None"),
    _fn("header", "header(level, title)", "Create a Discord embed field header.", ["level: int", "title: str"], "str"),
    _fn("randint", "randint(start, stop)", "Return a random integer N such that start <= N <= stop.", ["start: int", "stop: int"], "int"),
    _fn("rand", "rand()", "Return a random floating-point number in [0.0, 1.0).", [], "float"),
    _fn("sqrt", "sqrt(x)", "Return the square root of x.", ["x: int | float"], "float"),
    _fn("argparse", "argparse(args)", "Parse an argument string into an AliasArgParser.\n\nCommon usage:\n```\nargs = argparse(&ARGS&)\ntarget = args.last('t', '').strip()\n```", ["args: str"], "AliasArgParser"),
    _fn("character", "character()", "Return the AliasCharacter object for the active character.\n\nKey attributes:\n- `name` — character name\n- `hp` / `max_hp` / `temp_hp` — hit points\n- `ac` — armor class\n- `level` — total character level\n- `stats` — ability scores\n- `skills` — skill modifiers\n- `spells` — spellcasting info\n- `attacks` — list of attacks", [], "AliasCharacter"),
    _fn("combat", "combat()", "Return the AliasActiveCombat for the current combat, or None if not in combat.", [], "AliasActiveCombat | None"),
    _var("ctx", "ctx: AliasContext", "The context object for the current alias invocation.\n\nAttributes:\n- `author` — the Discord user who ran the alias\n- `channel` — the Discord channel\n- `guild` — the Discord server\n- `prefix` — the bot prefix used"),
]

BUILTINS: dict[str, BuiltinInfo] = {
    b.name: b for b in _DRACONIC_BUILTINS + _AVRAE_BUILTINS
}
