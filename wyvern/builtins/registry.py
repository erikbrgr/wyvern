"""
Registry of built-in names available in Draconic scripts, including:
- Draconic safe built-ins (subset of Python built-ins)
- Avrae aliasing API global functions and variables
- Class definitions for all Avrae API types (methods and properties)

Last verified against avrae/avrae@204c52b (nightly, 2026-06-09)
Source: https://github.com/avrae/avrae/tree/nightly/aliasing/api
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class BuiltinInfo:
    name: str
    kind: Literal["function", "variable", "class", "constant"]
    signature: str
    doc: str
    params: list[str] | None = None
    return_type: str | None = None


@dataclass
class ClassInfo:
    name: str
    doc: str
    bases: list[str] = field(default_factory=list)
    methods: list[BuiltinInfo] = field(default_factory=list)
    properties: list[BuiltinInfo] = field(default_factory=list)
    element_type: str | None = None


def _fn(name: str, sig: str, doc: str, params: list[str] | None = None, ret: str | None = None) -> BuiltinInfo:
    return BuiltinInfo(name, "function", sig, doc, params, ret)


def _cls(name: str, sig: str, doc: str, ret: str | None = None) -> BuiltinInfo:
    return BuiltinInfo(name, "class", sig, doc, None, ret)


def _var(name: str, sig: str, doc: str, ret: str | None = None) -> BuiltinInfo:
    return BuiltinInfo(name, "variable", sig, doc, None, ret)


def _const(name: str, doc: str) -> BuiltinInfo:
    return BuiltinInfo(name, "constant", name, doc)


def _prop(name: str, type_str: str, doc: str) -> BuiltinInfo:
    return BuiltinInfo(name, "variable", f"{name}: {type_str}", doc, None, type_str)


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
    _fn("range", "range(stop) | range(start, stop, step=1)", "Return a range object. Limited to 10,000 iterations.", ["start", "stop", "step=1"], "range"),
    _fn("reversed", "reversed(seq)", "Return a reverse iterator.", ["seq"], "reversed"),
    _fn("round", "round(number, ndigits=0)", "Round a number to a given precision.", ["number", "ndigits=0"], "float"),
    _fn("set", "set(iterable=())", "Return a new set object.", ["iterable=()"], "set"),
    _fn("sum", "sum(iterable, start=0)", "Sum the items of an iterable.", ["iterable", "start=0"], "int | float"),
    _fn("typeof", "typeof(x)", "Return the type name of x as a string. (Draconic alternative to type())", ["x"], "str"),
    _fn("zip", "zip(*iterables)", "Make an iterator that aggregates elements from each iterable.", ["*iterables"], "zip"),
    _cls("bool", "bool(x=False)", "Convert a value to Boolean."),
    _cls("dict", "dict(**kwargs)", "Create a new dictionary.", ret="dict"),
    _cls("float", "float(x=0.0)", "Convert a value to floating-point."),
    _cls("int", "int(x=0, base=10)", "Convert a value to integer."),
    _cls("list", "list(iterable=())", "Create a new list.", ret="list"),
    _cls("str", "str(object='')", "Convert a value to string.", ret="str"),
    _cls("tuple", "tuple(iterable=())", "Create a new tuple."),
    _const("True", "Boolean true constant."),
    _const("False", "Boolean false constant."),
    _const("None", "The None singleton."),
]

# ---------------------------------------------------------------------------
# Avrae Aliasing API — global functions and variables
# Source: aliasing/evaluators.py (ScriptingEvaluator) + aliasing/api/functions.py
# ---------------------------------------------------------------------------
_AVRAE_BUILTINS: list[BuiltinInfo] = [
    # --- Dice ---
    _fn("roll", "roll(dice)", "Roll a dice expression and return the total as an integer.\n\nExamples: `roll('1d20+5')`, `roll('2d6')`", ["dice: str"], "int"),
    _fn("vroll", "vroll(dice, multiply=1, add=0)", "Roll a dice expression verbosely and return a SimpleRollResult.\n\n`result.total` — the integer result\n`result.dice` — individual dice rolled\n`result.full` — full verbose output string\n`result.consolidated()` — simplified notation", ["dice: str", "multiply=1", "add=0"], "SimpleRollResult"),

    # --- Serialization ---
    _fn("load_json", "load_json(jsonstr)", "Parse a JSON string and return the corresponding Python object.", ["jsonstr: str"], "Any"),
    _fn("dump_json", "dump_json(obj)", "Serialize a Python object to a JSON string.", ["obj"], "str"),
    _fn("load_yaml", "load_yaml(yamlstr)", "Parse a YAML string and return the corresponding Python object.", ["yamlstr: str"], "Any"),
    _fn("dump_yaml", "dump_yaml(obj)", "Serialize a Python object to a YAML string.", ["obj"], "str"),

    # --- Variables: global ---
    _fn("get_gvar", "get_gvar(address)", "Fetch the value of a global variable (GVAR) by its address UUID.", ["address: str"], "str"),

    # --- Variables: user ---
    _fn("set_uvar", "set_uvar(name, value)", "Set a user variable. Value is stored as a string.", ["name: str", "value: str"], "None"),
    _fn("get_uvar", "get_uvar(name, default=None)", "Get a user variable. Returns default if not set.", ["name: str", "default=None"], "str | None"),
    _fn("delete_uvar", "delete_uvar(name)", "Delete a user variable.", ["name: str"], "None"),
    _fn("set_uvar_nx", "set_uvar_nx(name, value)", "Set a user variable only if it is not already set.", ["name: str", "value: str"], "None"),
    _fn("uvar_exists", "uvar_exists(name)", "Return True if the user variable exists.", ["name: str"], "bool"),
    _fn("get_uvars", "get_uvars()", "Return a dict of all user variables for the current user.", [], "dict[str, str]"),

    # --- Variables: server ---
    _fn("get_svar", "get_svar(name, default=None)", "Get a server variable. Returns default if not set.", ["name: str", "default=None"], "str | None"),

    # --- Utilities ---
    _fn("exists", "exists(name)", "Return True if the variable `name` is defined in the current scope.", ["name: str"], "bool"),
    _fn("get", "get(name, default=None)", "Return the value of `name` from the current scope, or `default` if not defined.", ["name: str", "default=None"], "Any"),
    _fn("err", "err(msg)", "Raise an error and stop alias execution with the given message.", ["msg: str"], "None"),
    # --- Random ---
    _fn("rand", "rand()", "Return a random floating-point number in [0.0, 1.0).", [], "float"),
    _fn("randint", "randint(start, stop=None, step=1)", "Return a random integer in the given range.\n\n`randint(n)` → random int in [0, n)\n`randint(a, b)` → random int in [a, b]\n`randint(a, b, step)` → random int in [a, b] with step", ["start: int", "stop=None", "step=1"], "int"),
    _fn("randchoice", "randchoice(seq)", "Return a single random element from the sequence.", ["seq"], "Any"),
    _fn("randchoices", "randchoices(population, weights=None, cum_weights=None, k=1)", "Return a list of `k` random elements from `population`, with optional weighting.", ["population", "weights=None", "cum_weights=None", "k=1"], "list"),

    # --- Math ---
    _fn("sqrt", "sqrt(x)", "Return the square root of x.", ["x: int | float"], "float"),

    # --- Coins ---
    _fn("parse_coins", "parse_coins(args, include_total=True)", "Parse a coin notation string into a dict of denominations.\n\nExample: `parse_coins('1pp 5gp 3cp')` → `{'pp': 1, 'gp': 5, 'ep': 0, 'sp': 0, 'cp': 3, 'total': 15.53}`", ["args: str", "include_total=True"], "dict"),

    # --- Argument parsing ---
    _fn("argparse", "argparse(args)", "Parse an argument string into an AliasArgParser.\n\nCommon usage:\n```\nargs = argparse(&ARGS&)\ntarget = args.last('t', '').strip()\nhas_adv = args.adv()\n```", ["args: str"], "AliasArgParser"),

    # --- Signature (workshop aliases) ---
    _fn("verify_signature", "verify_signature(ctx, data)", "Validate and decode a signature token, returning embedded metadata.", ["ctx", "data: str"], "dict"),

    # --- Script import ---
    _fn("using", "using(**kwargs)", "Import a script by GVAR UUID into the current scope.\n\nExample: `using(mylib='abc123-...')`", ["**kwargs"], "None"),

    # --- Game objects ---
    _fn("character", "character()", "Return the AliasCharacter for the active character.\n\nCall character methods to read/write HP, custom counters, CVARs, etc.", [], "AliasCharacter"),
    _fn("combat", "combat()", "Return the SimpleCombat for the current combat, or None if not in combat.", [], "SimpleCombat | None"),
    _var("ctx", "ctx: AliasContext", "The context object for the current alias invocation.\n\nAttributes: `ctx.author`, `ctx.channel`, `ctx.guild`, `ctx.prefix`, `ctx.alias`, `ctx.message_id`", "AliasContext"),
]


# ---------------------------------------------------------------------------
# Draconic built-in type methods
# Instance methods accessible on Draconic list/dict/str/set values.
# ---------------------------------------------------------------------------

_LIST_METHODS = [
    _fn("append", "append(x)", "Add item to the end of the list.", ["x"], "None"),
    _fn("clear", "clear()", "Remove all items from the list.", [], "None"),
    _fn("copy", "copy()", "Return a shallow copy of the list.", [], "list"),
    _fn("count", "count(x)", "Return the number of times x appears.", ["x"], "int"),
    _fn("extend", "extend(iterable)", "Extend the list by appending all items from the iterable.", ["iterable"], "None"),
    _fn("index", "index(x, start=0, stop=None)", "Return the index of the first occurrence of x.", ["x", "start=0", "stop=None"], "int"),
    _fn("insert", "insert(i, x)", "Insert x before position i.", ["i", "x"], "None"),
    _fn("pop", "pop(i=-1)", "Remove and return the item at position i.", ["i=-1"], "Any"),
    _fn("remove", "remove(x)", "Remove the first occurrence of x.", ["x"], "None"),
    _fn("reverse", "reverse()", "Reverse the list in place.", [], "None"),
    _fn("sort", "sort(key=None, reverse=False)", "Sort the list in place.", ["key=None", "reverse=False"], "None"),
]

_DICT_METHODS = [
    _fn("clear", "clear()", "Remove all items from the dictionary.", [], "None"),
    _fn("copy", "copy()", "Return a shallow copy of the dictionary.", [], "dict"),
    _fn("get", "get(key, default=None)", "Return the value for key if present, else default.", ["key", "default=None"], "Any"),
    _fn("items", "items()", "Return a view of the dictionary's (key, value) pairs.", [], "Any"),
    _fn("keys", "keys()", "Return a view of the dictionary's keys.", [], "Any"),
    _fn("pop", "pop(key, default=None)", "Remove and return the value for key.", ["key", "default=None"], "Any"),
    _fn("update", "update(other)", "Update the dictionary with key/value pairs from other.", ["other"], "None"),
    _fn("values", "values()", "Return a view of the dictionary's values.", [], "Any"),
]

_STR_METHODS = [
    _fn("capitalize", "capitalize()", "Return the string with its first character capitalized.", [], "str"),
    _fn("count", "count(sub, start=0, stop=None)", "Return the number of occurrences of sub.", ["sub", "start=0", "stop=None"], "int"),
    _fn("endswith", "endswith(suffix)", "Return True if the string ends with suffix.", ["suffix"], "bool"),
    _fn("find", "find(sub, start=0, stop=None)", "Return the lowest index where sub is found, or -1.", ["sub", "start=0", "stop=None"], "int"),
    _fn("format", "format(*args, **kwargs)", "Return a formatted version of the string.", ["*args", "**kwargs"], "str"),
    _fn("index", "index(sub, start=0, stop=None)", "Like find(), but raise ValueError when sub is not found.", ["sub", "start=0", "stop=None"], "int"),
    _fn("isdigit", "isdigit()", "Return True if all characters are digits.", [], "bool"),
    _fn("isalpha", "isalpha()", "Return True if all characters are alphabetic.", [], "bool"),
    _fn("join", "join(iterable)", "Return a string joining the elements of iterable with this string as separator.", ["iterable"], "str"),
    _fn("lower", "lower()", "Return the string in lowercase.", [], "str"),
    _fn("lstrip", "lstrip(chars=None)", "Return the string with leading whitespace (or chars) removed.", ["chars=None"], "str"),
    _fn("replace", "replace(old, new, count=-1)", "Return the string with all occurrences of old replaced by new.", ["old", "new", "count=-1"], "str"),
    _fn("rstrip", "rstrip(chars=None)", "Return the string with trailing whitespace (or chars) removed.", ["chars=None"], "str"),
    _fn("split", "split(sep=None, maxsplit=-1)", "Return a list of the words in the string.", ["sep=None", "maxsplit=-1"], "list"),
    _fn("splitlines", "splitlines(keepends=False)", "Return a list of the lines in the string.", ["keepends=False"], "list"),
    _fn("startswith", "startswith(prefix)", "Return True if the string starts with prefix.", ["prefix"], "bool"),
    _fn("strip", "strip(chars=None)", "Return the string with leading and trailing whitespace (or chars) removed.", ["chars=None"], "str"),
    _fn("title", "title()", "Return the string in title case.", [], "str"),
    _fn("upper", "upper()", "Return the string in uppercase.", [], "str"),
    _fn("zfill", "zfill(width)", "Pad the string on the left with zeros to the given width.", ["width"], "str"),
]

_SET_METHODS = [
    _fn("add", "add(elem)", "Add element elem to the set.", ["elem"], "None"),
    _fn("clear", "clear()", "Remove all elements from the set.", [], "None"),
    _fn("copy", "copy()", "Return a shallow copy of the set.", [], "set"),
    _fn("difference", "difference(*others)", "Return a new set with elements not in the others.", ["*others"], "set"),
    _fn("discard", "discard(elem)", "Remove elem from the set if present.", ["elem"], "None"),
    _fn("intersection", "intersection(*others)", "Return a new set with elements common to this and all others.", ["*others"], "set"),
    _fn("issubset", "issubset(other)", "Return True if every element of this set is in other.", ["other"], "bool"),
    _fn("issuperset", "issuperset(other)", "Return True if every element of other is in this set.", ["other"], "bool"),
    _fn("pop", "pop()", "Remove and return an arbitrary element.", [], "Any"),
    _fn("remove", "remove(elem)", "Remove elem from the set. Raises KeyError if not present.", ["elem"], "None"),
    _fn("union", "union(*others)", "Return a new set with elements from this set and all others.", ["*others"], "set"),
    _fn("update", "update(*others)", "Update the set, adding elements from all others.", ["*others"], "None"),
]

# ---------------------------------------------------------------------------
# Avrae API class registry
# Each entry describes the methods and properties available on an API type.
# Used for attribute-access completion and hover in the LSP.
# ---------------------------------------------------------------------------

_SIMPLE_ROLL_RESULT_METHODS = [
    _fn("consolidated", "consolidated()", "Return a simplified roll string with totals and damage types grouped.", [], "str"),
]
_SIMPLE_ROLL_RESULT_PROPS = [
    _prop("dice", "str", "Markdown-formatted dice notation string."),
    _prop("total", "int", "Numeric total of the roll."),
    _prop("full", "str", "Full verbose roll output string."),
    _prop("result", "Any", "The underlying d20.RollResult object."),
    _prop("raw", "Any", "The raw expression AST."),
]

_ALIAS_ARG_PARSER_METHODS = [
    _fn("last", "last(flag, default='', type_=str)", "Return the last value provided for `flag`, cast to `type_`. Returns `default` if the flag was not supplied.", ["flag: str", "default=''", "type_=str"], "Any"),
    _fn("get", "get(flag, default=[], type_=str)", "Return a list of all values provided for `flag`, each cast to `type_`. Returns `default` if not supplied.", ["flag: str", "default=[]", "type_=str"], "list"),
    _fn("adv", "adv(eadv=False, boolwise=False, ephem=False)", "Check advantage/disadvantage flags (`adv`/`dis`/`ea`).\n\nReturns 1 for advantage, -1 for disadvantage, 0 for neither.\nWith `boolwise=True` returns True/False/None.", ["eadv=False", "boolwise=False", "ephem=False"], "int"),
    _fn("join", "join(flag, connector, default='')", "Join all values for `flag` with `connector`. Returns `default` if not supplied.", ["flag: str", "connector: str", "default=''"], "str"),
    _fn("ignore", "ignore(flag)", "Mark `flag` as consumed so it does not appear in leftover args.", ["flag: str"], "None"),
    _fn("bool", "bool(flag, default=False)", "Return True if `flag` is present, False if explicitly denied, or `default` otherwise.", ["flag: str", "default=False"], "bool"),
]
_ALIAS_ARG_PARSER_PROPS = [
    _prop("unparsed", "list[str]", "List of positional / unrecognized argument tokens."),
]

_SIMPLE_COMBAT_METHODS = [
    _fn("get_combatant", "get_combatant(name, strict=None)", "Return the SimpleCombatant with the given name, or None. Pass `strict=True` to require an exact match.", ["name: str", "strict=None"], "SimpleCombatant | None"),
    _fn("get_group", "get_group(name, strict=None)", "Return the SimpleGroup with the given name, or None.", ["name: str", "strict=None"], "SimpleGroup | None"),
    _fn("set_metadata", "set_metadata(k, v)", "Store a string value `v` under key `k` on the combat. Persists until combat ends.", ["k: str", "v: str"], "None"),
    _fn("get_metadata", "get_metadata(k, default=None)", "Retrieve the value stored under key `k`, or `default` if not set.", ["k: str", "default=None"], "str | None"),
    _fn("delete_metadata", "delete_metadata(k)", "Remove the metadata entry for key `k`. Returns the old value, or None.", ["k: str"], "str | None"),
    _fn("set_round", "set_round(round_num)", "Set the current round number.", ["round_num: int"], "None"),
    _fn("end_round", "end_round()", "Advance to the end of the current round, triggering end-of-round effects.", [], "None"),
]
_SIMPLE_COMBAT_PROPS = [
    _prop("combatants", "list[SimpleCombatant]", "All combatants currently in the combat (not inside groups)."),
    _prop("groups", "list[SimpleGroup]", "All combatant groups in the combat."),
    _prop("me", "SimpleCombatant | None", "The combatant representing the character running this alias, or None."),
    _prop("round_num", "int", "The current round number."),
    _prop("turn_num", "int", "The index of the current turn within the round."),
    _prop("current", "SimpleCombatant | None", "The combatant whose turn it currently is."),
    _prop("name", "str", "The name of this combat instance."),
]

_SIMPLE_COMBATANT_METHODS = [
    _fn("save", "save(ability, adv=None)", "Roll a saving throw for this combatant and return the result string.", ["ability: str", "adv=None"], "str"),
    _fn("damage", "damage(dice_str, crit=False, d=None, c=None, critdice=0, overheal=False)", "Deal damage to this combatant and return a result string.", ["dice_str: str", "crit=False", "d=None", "c=None", "critdice=0", "overheal=False"], "str"),
    _fn("set_ac", "set_ac(ac)", "Set this combatant's armor class.", ["ac: int"], "None"),
    _fn("set_maxhp", "set_maxhp(maxhp)", "Set this combatant's maximum HP.", ["maxhp: int"], "None"),
    _fn("set_init", "set_init(init)", "Set this combatant's initiative value.", ["init: int"], "None"),
    _fn("set_name", "set_name(name)", "Rename this combatant.", ["name: str"], "None"),
    _fn("set_group", "set_group(group)", "Move this combatant into the named group (or remove from group if None).", ["group: str | None"], "None"),
    _fn("set_note", "set_note(note)", "Set a note on this combatant.", ["note: str | None"], "None"),
    _fn("get_effect", "get_effect(name, strict=False)", "Return the SimpleEffect with the given name, or None.", ["name: str", "strict=False"], "SimpleEffect | None"),
    _fn("add_effect", "add_effect(name, args=None, duration=None, concentration=False, parent=None, end=False, desc=None, passive_effects=None, attacks=None, buttons=None, tick_on_combatant_id=None)", "Add an effect to this combatant and return it.", ["name: str", "args=None", "duration=None", "concentration=False", "parent=None", "end=False", "desc=None", "passive_effects=None", "attacks=None", "buttons=None", "tick_on_combatant_id=None"], "SimpleEffect"),
    _fn("remove_effect", "remove_effect(name, strict=False)", "Remove the named effect from this combatant.", ["name: str", "strict=False"], "None"),
]
_SIMPLE_COMBATANT_OWN_PROPS = [
    _prop("id", "str", "Unique combatant ID (UUID)."),
    _prop("note", "str | None", "Note attached to this combatant, or None."),
    _prop("controller", "int", "Discord user ID of the player controlling this combatant."),
    _prop("group", "str | None", "Name of the group this combatant belongs to, or None."),
    _prop("race", "str | None", "Race of this combatant, if known."),
    _prop("monster_name", "str | None", "Monster type name for monster combatants, or None for PCs."),
    _prop("is_hidden", "bool", "True if this combatant is hidden from other players."),
    _prop("effects", "list[SimpleEffect]", "All effects currently applied to this combatant."),
]

_SIMPLE_GROUP_METHODS = [
    _fn("get_combatant", "get_combatant(name, strict=None)", "Return the SimpleCombatant in this group with the given name, or None.", ["name: str", "strict=None"], "SimpleCombatant | None"),
    _fn("set_init", "set_init(init)", "Set the initiative value for the entire group.", ["init: int"], "None"),
]
_SIMPLE_GROUP_PROPS = [
    _prop("name", "str", "Name of this group."),
    _prop("id", "str", "Unique group ID (UUID)."),
    _prop("combatants", "list[SimpleCombatant]", "Combatants inside this group."),
    _prop("init", "int", "Initiative value of this group."),
    _prop("type", "str", "Type string, always 'group'."),
]

_SIMPLE_EFFECT_METHODS = [
    _fn("set_parent", "set_parent(parent)", "Set the parent effect of this effect.", ["parent: SimpleEffect"], "None"),
]
_SIMPLE_EFFECT_PROPS = [
    _prop("name", "str", "Name of the effect."),
    _prop("duration", "int | None", "Total duration in rounds, or None if indefinite."),
    _prop("remaining", "int | None", "Rounds remaining, or None if indefinite."),
    _prop("effect", "dict", "Effect data dict (passive bonuses, etc.)."),
    _prop("attacks", "list", "List of extra attacks granted by this effect."),
    _prop("buttons", "list", "List of button interactions attached to this effect."),
    _prop("conc", "bool", "True if this effect requires concentration."),
    _prop("desc", "str | None", "Description of the effect."),
    _prop("ticks_on_end", "bool", "True if this effect ticks at the end of the combatant's turn."),
    _prop("combatant_name", "str", "Name of the combatant this effect is attached to."),
    _prop("parent", "SimpleEffect | None", "Parent effect, or None."),
    _prop("children", "list[SimpleEffect]", "Child effects of this effect."),
]

_ALIAS_STAT_BLOCK_METHODS = [
    _fn("set_hp", "set_hp(new_hp)", "Set the current HP of this statblock.", ["new_hp: int"], "None"),
    _fn("modify_hp", "modify_hp(amount, ignore_temp=False, overflow=True)", "Modify HP by `amount` (positive = heal, negative = damage). Returns a summary string.", ["amount: int", "ignore_temp=False", "overflow=True"], "str"),
    _fn("hp_str", "hp_str()", "Return a formatted HP string, e.g. '45/60'.", [], "str"),
    _fn("reset_hp", "reset_hp()", "Restore HP to max.", [], "None"),
    _fn("set_temp_hp", "set_temp_hp(new_temp)", "Set the temporary HP of this statblock.", ["new_temp: int"], "None"),
]
_ALIAS_STAT_BLOCK_PROPS = [
    _prop("name", "str", "Name of this creature or character."),
    _prop("stats", "AliasBaseStats", "Ability scores and proficiency bonus."),
    _prop("levels", "AliasLevels", "Class levels (for characters) or CR (for monsters)."),
    _prop("attacks", "AliasAttackList", "List of attacks available to this statblock."),
    _prop("skills", "AliasSkills", "Skill modifiers keyed by skill name."),
    _prop("saves", "AliasSaves", "Saving throw modifiers keyed by ability."),
    _prop("resistances", "AliasResistances", "Damage resistances, immunities, and vulnerabilities."),
    _prop("ac", "int | None", "Armor class, or None if not set."),
    _prop("max_hp", "int | None", "Maximum hit points, or None if not set."),
    _prop("hp", "int | None", "Current hit points, or None if not set."),
    _prop("temp_hp", "int", "Temporary hit points (0 if none)."),
    _prop("spellbook", "AliasSpellbook", "Spellcasting information for this statblock."),
    _prop("creature_type", "str | None", "Creature type string (e.g. 'humanoid'), or None."),
]

_ALIAS_CHARACTER_METHODS = _ALIAS_STAT_BLOCK_METHODS + [
    _fn("cc", "cc(name)", "Return the AliasCustomCounter with the given name. Raises error if not found.", ["name: str"], "AliasCustomCounter"),
    _fn("get_cc", "get_cc(name)", "Return the current value of the named custom counter.", ["name: str"], "int"),
    _fn("get_cc_max", "get_cc_max(name)", "Return the maximum value of the named custom counter, or None.", ["name: str"], "int | None"),
    _fn("get_cc_min", "get_cc_min(name)", "Return the minimum value of the named custom counter, or None.", ["name: str"], "int | None"),
    _fn("set_cc", "set_cc(name, value, strict=False)", "Set the named custom counter to `value`.", ["name: str", "value: int", "strict=False"], "None"),
    _fn("mod_cc", "mod_cc(name, val, strict=False)", "Modify the named custom counter by `val`.", ["name: str", "val: int", "strict=False"], "None"),
    _fn("delete_cc", "delete_cc(name)", "Delete the named custom counter.", ["name: str"], "None"),
    _fn("create_cc_nx", "create_cc_nx(name, minVal=None, maxVal=None, reset=None, dispType=None, reset_to=None, reset_by=None, title=None, desc=None, initial_value=None)", "Create a custom counter only if one with that name does not already exist.", ["name: str", "minVal=None", "maxVal=None", "reset=None", "dispType=None", "reset_to=None", "reset_by=None", "title=None", "desc=None", "initial_value=None"], "AliasCustomCounter"),
    _fn("create_cc", "create_cc(name, minVal=None, maxVal=None, reset=None, dispType=None, reset_to=None, reset_by=None, title=None, desc=None, initial_value=None)", "Create (or recreate) a custom counter with the given parameters.", ["name: str", "minVal=None", "maxVal=None", "reset=None", "dispType=None", "reset_to=None", "reset_by=None", "title=None", "desc=None", "initial_value=None"], "AliasCustomCounter"),
    _fn("edit_cc", "edit_cc(name, minVal=None, maxVal=None, reset=None, dispType=None, reset_to=None, reset_by=None, title=None, desc=None, new_name=None)", "Edit an existing custom counter's properties.", ["name: str", "minVal=None", "maxVal=None", "reset=None", "dispType=None", "reset_to=None", "reset_by=None", "title=None", "desc=None", "new_name=None"], "None"),
    _fn("cc_exists", "cc_exists(name)", "Return True if a custom counter with the given name exists.", ["name: str"], "bool"),
    _fn("cc_str", "cc_str(name)", "Return a formatted string representation of the named custom counter.", ["name: str"], "str"),
    _fn("get_cvar", "get_cvar(name, default=None)", "Get a character variable. Returns default if not set.", ["name: str", "default=None"], "str | None"),
    _fn("set_cvar", "set_cvar(name, val)", "Set a character variable. Value is stored as a string.", ["name: str", "val: str"], "None"),
    _fn("set_cvar_nx", "set_cvar_nx(name, val)", "Set a character variable only if it is not already set.", ["name: str", "val: str"], "None"),
    _fn("delete_cvar", "delete_cvar(name)", "Delete a character variable.", ["name: str"], "None"),
]
_ALIAS_CHARACTER_PROPS = _ALIAS_STAT_BLOCK_PROPS + [
    _prop("consumables", "list[AliasCustomCounter]", "All custom counters on this character."),
    _prop("cvars", "dict[str, str]", "All character variables as a dict."),
    _prop("death_saves", "AliasDeathSaves", "Death save state for this character."),
    _prop("actions", "list[AliasAction]", "All actions available to this character."),
    _prop("owner", "int", "Discord user ID of the character's owner."),
    _prop("upstream", "str", "The upstream source ID (e.g. D&D Beyond URL)."),
    _prop("sheet_type", "str", "Sheet type identifier (e.g. 'beyond', 'dicecloud')."),
    _prop("race", "str | None", "Character race, or None."),
    _prop("background", "str | None", "Character background, or None."),
    _prop("csettings", "dict", "Character-level settings dict."),
    _prop("coinpurse", "AliasCoinpurse", "The character's coin purse."),
    _prop("description", "str | None", "Character description, or None."),
    _prop("image", "str | None", "URL to character portrait image, or None."),
]

_ALIAS_CUSTOM_COUNTER_METHODS = [
    _fn("mod", "mod(value, strict=False)", "Modify the counter value by `value`.", ["value: int", "strict=False"], "None"),
    _fn("set", "set(new_value, strict=False)", "Set the counter to `new_value`.", ["new_value: int", "strict=False"], "None"),
    _fn("reset", "reset()", "Reset the counter to its reset value.", [], "None"),
    _fn("full_str", "full_str(include_name=False)", "Return a formatted string showing value, min, and max.", ["include_name=False"], "str"),
]
_ALIAS_CUSTOM_COUNTER_PROPS = [
    _prop("name", "str", "Name of this counter."),
    _prop("title", "str", "Display title of this counter (may differ from name)."),
    _prop("desc", "str | None", "Description of this counter."),
    _prop("value", "int", "Current value."),
    _prop("max", "int | None", "Maximum value, or None if no max."),
    _prop("min", "int | None", "Minimum value, or None if no min."),
    _prop("reset_on", "str | None", "Reset trigger: 'short', 'long', 'hp', 'none', or None."),
    _prop("display_type", "str | None", "Display type: 'star', 'bubble', or None for default bar."),
    _prop("reset_to", "int | None", "Value to reset to, or None for max."),
    _prop("reset_by", "str | None", "Expression to reset by (e.g. '+1d6'), or None."),
]

_ALIAS_DEATH_SAVES_METHODS = [
    _fn("succeed", "succeed(num=1)", "Add `num` death save successes.", ["num=1"], "None"),
    _fn("fail", "fail(num=1)", "Add `num` death save failures.", ["num=1"], "None"),
    _fn("is_stable", "is_stable()", "Return True if the character is stable (3 successes).", [], "bool"),
    _fn("is_dead", "is_dead()", "Return True if the character is dead (3 failures).", [], "bool"),
    _fn("reset", "reset()", "Reset all death saves.", [], "None"),
]
_ALIAS_DEATH_SAVES_PROPS = [
    _prop("successes", "int", "Number of death save successes (0–3)."),
    _prop("fails", "int", "Number of death save failures (0–3)."),
]

_ALIAS_ACTION_PROPS = [
    _prop("name", "str", "Name of this action."),
    _prop("activation_type", "int | None", "Numeric activation type code, or None."),
    _prop("activation_type_name", "str | None", "Human-readable activation type (e.g. 'Action', 'Bonus Action'), or None."),
    _prop("description", "str | None", "Full description text of this action, or None."),
    _prop("snippet", "str | None", "Automation snippet for this action, or None."),
]

_ALIAS_COINPURSE_METHODS = [
    _fn("coin_str", "coin_str(cointype)", "Return a formatted string for the given coin type (e.g. 'gp').", ["cointype: str"], "str"),
    _fn("compact_str", "compact_str()", "Return a compact string showing all non-zero coin amounts.", [], "str"),
    _fn("modify_coins", "modify_coins(pp=0, gp=0, ep=0, sp=0, cp=0, autoconvert=True)", "Add or subtract coins. Returns self.", ["pp=0", "gp=0", "ep=0", "sp=0", "cp=0", "autoconvert=True"], "AliasCoinpurse"),
    _fn("set_coins", "set_coins(pp, gp, ep, sp, cp)", "Set absolute coin amounts. Returns self.", ["pp: int", "gp: int", "ep: int", "sp: int", "cp: int"], "AliasCoinpurse"),
    _fn("autoconvert", "autoconvert()", "Automatically convert smaller coins to larger denominations. Returns self.", [], "AliasCoinpurse"),
    _fn("get_coins", "get_coins()", "Return a dict of all coin amounts: {'pp': ..., 'gp': ..., 'ep': ..., 'sp': ..., 'cp': ...}.", [], "dict"),
]
_ALIAS_COINPURSE_PROPS = [
    _prop("total", "float", "Total coin value in gold pieces."),
    _prop("pp", "int", "Platinum pieces."),
    _prop("gp", "int", "Gold pieces."),
    _prop("ep", "int", "Electrum pieces."),
    _prop("sp", "int", "Silver pieces."),
    _prop("cp", "int", "Copper pieces."),
]

_ALIAS_CONTEXT_PROPS = [
    _prop("guild", "AliasGuild | None", "The Discord server this alias ran in, or None in DMs."),
    _prop("channel", "AliasChannel", "The Discord channel this alias ran in."),
    _prop("author", "AliasAuthor", "The Discord user who invoked this alias."),
    _prop("prefix", "str", "The command prefix used (e.g. '!')."),
    _prop("alias", "str", "The name of the alias that was invoked."),
    _prop("message_id", "int", "Snowflake ID of the triggering message."),
    _prop("reply_to_id", "int | None", "Snowflake ID of the message being replied to, or None."),
]

_ALIAS_GUILD_METHODS = [
    _fn("servsettings", "servsettings()", "Return the server's Avrae settings dict, or None.", [], "dict | None"),
]
_ALIAS_GUILD_PROPS = [
    _prop("name", "str", "Server name."),
    _prop("id", "int", "Server snowflake ID."),
]

_ALIAS_CHANNEL_PROPS = [
    _prop("name", "str", "Channel name (without #)."),
    _prop("id", "int", "Channel snowflake ID."),
    _prop("topic", "str | None", "Channel topic text, or None."),
    _prop("category", "AliasCategory | None", "Parent category, or None if uncategorized."),
    _prop("parent", "AliasChannel | None", "Parent channel for threads, or None."),
]

_ALIAS_AUTHOR_METHODS = [
    _fn("get_roles", "get_roles()", "Return a list of AliasRole objects for all roles this user has in the server.", [], "list[AliasRole]"),
]
_ALIAS_AUTHOR_PROPS = [
    _prop("name", "str", "The user's username (not display name)."),
    _prop("id", "int", "The user's snowflake ID."),
    _prop("discriminator", "str", "The user's discriminator (e.g. '0' for new usernames)."),
    _prop("display_name", "str", "The user's display name in this server (nickname if set, else username)."),
]

_ALIAS_ROLE_PROPS = [
    _prop("name", "str", "Role name."),
    _prop("id", "int", "Role snowflake ID."),
]

_ALIAS_CATEGORY_PROPS = [
    _prop("name", "str", "Category name."),
    _prop("id", "int", "Category snowflake ID."),
]

_ALIAS_BASE_STATS_METHODS = [
    _fn("get_mod", "get_mod(stat)", "Return the ability modifier for `stat` (e.g. 'strength', 'str').", ["stat: str"], "int"),
    _fn("get", "get(stat)", "Return the raw ability score for `stat`.", ["stat: str"], "int"),
]
_ALIAS_BASE_STATS_PROPS = [
    _prop("prof_bonus", "int", "Proficiency bonus."),
    _prop("strength", "int", "Strength score."),
    _prop("dexterity", "int", "Dexterity score."),
    _prop("constitution", "int", "Constitution score."),
    _prop("intelligence", "int", "Intelligence score."),
    _prop("wisdom", "int", "Wisdom score."),
    _prop("charisma", "int", "Charisma score."),
]

_ALIAS_LEVELS_METHODS = [
    _fn("get", "get(cls_name, default=0)", "Return the number of levels in the given class, or `default`.", ["cls_name: str", "default=0"], "int"),
]
_ALIAS_LEVELS_PROPS = [
    _prop("total_level", "int", "Total character level (sum of all class levels)."),
]


_ALIAS_ATTACK_PROPS = [
    _prop("name", "str", "Attack name."),
    _prop("verb", "str | None", "Verb used in attack description (e.g. 'attacks with'), or None."),
    _prop("proper", "bool", "True if the attack name is a proper noun."),
    _prop("activation_type", "int", "Numeric activation type for this attack."),
    _prop("raw", "dict", "Raw attack data dict."),
]

_ALIAS_SKILL_METHODS = [
    _fn("d20", "d20(base_adv=None, reroll=None, min_val=None, mod_override=None)", "Return a formatted d20 roll string using this skill's modifier.", ["base_adv=None", "reroll=None", "min_val=None", "mod_override=None"], "str"),
]
_ALIAS_SKILL_PROPS = [
    _prop("value", "int", "Total skill modifier (ability mod + proficiency + bonus)."),
    _prop("prof", "float | int", "Proficiency multiplier (0, 0.5, 1, or 2)."),
    _prop("bonus", "int", "Additional flat bonus beyond proficiency."),
    _prop("adv", "bool | None", "Advantage override: True, False, or None."),
]

_ALIAS_RESISTANCES_METHODS = [
    _fn("is_resistant", "is_resistant(damage_type)", "Return True if this statblock is resistant to `damage_type`.", ["damage_type: str"], "bool"),
    _fn("is_immune", "is_immune(damage_type)", "Return True if this statblock is immune to `damage_type`.", ["damage_type: str"], "bool"),
    _fn("is_vulnerable", "is_vulnerable(damage_type)", "Return True if this statblock is vulnerable to `damage_type`.", ["damage_type: str"], "bool"),
    _fn("is_neutral", "is_neutral(damage_type)", "Return True if this statblock has explicitly neutral damage for `damage_type`.", ["damage_type: str"], "bool"),
]
_ALIAS_RESISTANCES_PROPS = [
    _prop("resist", "list[str]", "Damage types this statblock is resistant to."),
    _prop("vuln", "list[str]", "Damage types this statblock is vulnerable to."),
    _prop("immune", "list[str]", "Damage types this statblock is immune to."),
    _prop("neutral", "list[str]", "Damage types explicitly marked as neutral."),
]

_ALIAS_SPELLBOOK_METHODS = [
    _fn("find", "find(spell_name)", "Search prepared spells by name (partial match). Returns matching AliasSpellbookSpell list.", ["spell_name: str"], "list[AliasSpellbookSpell]"),
    _fn("slots_str", "slots_str(level)", "Return a formatted string showing used/max spell slots at `level`.", ["level: int"], "str"),
    _fn("get_max_slots", "get_max_slots(level)", "Return the maximum number of spell slots at `level`.", ["level: int"], "int"),
    _fn("get_slots", "get_slots(level)", "Return the number of remaining spell slots at `level`.", ["level: int"], "int"),
    _fn("set_slots", "set_slots(level, value, pact=True)", "Set the number of remaining spell slots at `level`.", ["level: int", "value: int", "pact=True"], "None"),
    _fn("use_slot", "use_slot(level)", "Expend one spell slot at `level`.", ["level: int"], "None"),
    _fn("reset_slots", "reset_slots()", "Restore all spell slots (long rest).", [], "None"),
    _fn("reset_pact_slots", "reset_pact_slots()", "Restore pact magic slots only (short rest).", [], "None"),
    _fn("remaining_casts_of", "remaining_casts_of(spell, level)", "Return a string showing how many times `spell` can still be cast at `level`.", ["spell: str", "level: int"], "str"),
    _fn("cast", "cast(spell, level)", "Record that `spell` has been cast at `level`, expending a slot.", ["spell: str", "level: int"], "None"),
    _fn("can_cast", "can_cast(spell, level)", "Return True if there is a slot available to cast `spell` at `level`.", ["spell: str", "level: int"], "bool"),
]
_ALIAS_SPELLBOOK_PROPS = [
    _prop("dc", "int", "Spell save DC."),
    _prop("sab", "int", "Spell attack bonus."),
    _prop("caster_level", "int", "Caster level for slot progression."),
    _prop("spell_mod", "int", "Spellcasting ability modifier."),
    _prop("spells", "list[AliasSpellbookSpell]", "All spells in this spellbook."),
    _prop("pact_slot_level", "int | None", "Pact magic slot level, or None."),
    _prop("num_pact_slots", "int | None", "Current pact magic slots remaining, or None."),
    _prop("max_pact_slots", "int | None", "Maximum pact magic slots, or None."),
]

_ALIAS_SPELLBOOK_SPELL_PROPS = [
    _prop("name", "str", "Spell name."),
    _prop("dc", "int | None", "Override spell save DC, or None to use spellbook default."),
    _prop("sab", "int | None", "Override spell attack bonus, or None to use spellbook default."),
    _prop("mod", "int | None", "Override spellcasting ability modifier, or None to use spellbook default."),
    _prop("prepared", "bool", "True if this spell is prepared (always True for known-spell casters)."),
]


CLASS_REGISTRY: dict[str, ClassInfo] = {
    "list": ClassInfo(
        name="list",
        doc="Draconic list. Supports standard Python list methods.",
        methods=_LIST_METHODS,
    ),
    "dict": ClassInfo(
        name="dict",
        doc="Draconic dictionary. Supports standard Python dict methods.",
        methods=_DICT_METHODS,
    ),
    "str": ClassInfo(
        name="str",
        doc="Draconic string. Supports standard Python str methods.",
        methods=_STR_METHODS,
    ),
    "set": ClassInfo(
        name="set",
        doc="Draconic set. Supports standard Python set methods.",
        methods=_SET_METHODS,
    ),
    "SimpleRollResult": ClassInfo(
        name="SimpleRollResult",
        doc="Result of a `vroll()` call. Contains the dice notation, numeric total, and full verbose string.",
        methods=_SIMPLE_ROLL_RESULT_METHODS,
        properties=_SIMPLE_ROLL_RESULT_PROPS,
    ),
    "AliasArgParser": ClassInfo(
        name="AliasArgParser",
        doc="Parsed alias arguments, returned by `argparse()`. Use `.last()` for single values, `.get()` for lists, `.adv()` for advantage/disadvantage.",
        methods=_ALIAS_ARG_PARSER_METHODS,
        properties=_ALIAS_ARG_PARSER_PROPS,
    ),
    "SimpleCombat": ClassInfo(
        name="SimpleCombat",
        doc="The active combat tracker, returned by `combat()`. Also referred to as `AliasActiveCombat` in the Avrae documentation. Provides access to combatants, groups, and combat state.",
        methods=_SIMPLE_COMBAT_METHODS,
        properties=_SIMPLE_COMBAT_PROPS,
    ),
    "SimpleCombatant": ClassInfo(
        name="SimpleCombatant",
        doc="A single combatant in the active combat. Inherits all AliasStatBlock properties and methods.",
        bases=["AliasStatBlock"],
        methods=_SIMPLE_COMBATANT_METHODS,
        properties=_SIMPLE_COMBATANT_OWN_PROPS,
    ),
    "SimpleGroup": ClassInfo(
        name="SimpleGroup",
        doc="A group of combatants in the active combat.",
        methods=_SIMPLE_GROUP_METHODS,
        properties=_SIMPLE_GROUP_PROPS,
    ),
    "SimpleEffect": ClassInfo(
        name="SimpleEffect",
        doc="An effect (condition, buff, debuff) applied to a combatant.",
        methods=_SIMPLE_EFFECT_METHODS,
        properties=_SIMPLE_EFFECT_PROPS,
    ),
    "AliasStatBlock": ClassInfo(
        name="AliasStatBlock",
        doc="Base class for creatures and characters. Provides HP, stats, attacks, skills, saves, resistances, and spellcasting.",
        methods=_ALIAS_STAT_BLOCK_METHODS,
        properties=_ALIAS_STAT_BLOCK_PROPS,
    ),
    "AliasCharacter": ClassInfo(
        name="AliasCharacter",
        doc="The active player character, returned by `character()`. Inherits AliasStatBlock and adds custom counters, CVARs, death saves, actions, and coinpurse.",
        bases=["AliasStatBlock"],
        methods=_ALIAS_CHARACTER_METHODS,
        properties=_ALIAS_CHARACTER_PROPS,
    ),
    "AliasCustomCounter": ClassInfo(
        name="AliasCustomCounter",
        doc="A custom counter (limited-use resource) on a character. Access via `character().cc('name')` or iterate `character().consumables`.",
        methods=_ALIAS_CUSTOM_COUNTER_METHODS,
        properties=_ALIAS_CUSTOM_COUNTER_PROPS,
    ),
    "AliasDeathSaves": ClassInfo(
        name="AliasDeathSaves",
        doc="Death save state for a character. Access via `character().death_saves`.",
        methods=_ALIAS_DEATH_SAVES_METHODS,
        properties=_ALIAS_DEATH_SAVES_PROPS,
    ),
    "AliasAction": ClassInfo(
        name="AliasAction",
        doc="A character action (from features, items, etc.). Access via `character().actions`.",
        properties=_ALIAS_ACTION_PROPS,
    ),
    "AliasCoinpurse": ClassInfo(
        name="AliasCoinpurse",
        doc="A character's coin purse. Access via `character().coinpurse`.",
        methods=_ALIAS_COINPURSE_METHODS,
        properties=_ALIAS_COINPURSE_PROPS,
    ),
    "AliasContext": ClassInfo(
        name="AliasContext",
        doc="Discord context for the current alias invocation. Available as the global `ctx` variable.",
        properties=_ALIAS_CONTEXT_PROPS,
    ),
    "AliasGuild": ClassInfo(
        name="AliasGuild",
        doc="The Discord server (guild) the alias ran in. Access via `ctx.guild`.",
        methods=_ALIAS_GUILD_METHODS,
        properties=_ALIAS_GUILD_PROPS,
    ),
    "AliasChannel": ClassInfo(
        name="AliasChannel",
        doc="A Discord channel or thread. Access via `ctx.channel`.",
        properties=_ALIAS_CHANNEL_PROPS,
    ),
    "AliasAuthor": ClassInfo(
        name="AliasAuthor",
        doc="The Discord user who invoked the alias. Access via `ctx.author`.",
        methods=_ALIAS_AUTHOR_METHODS,
        properties=_ALIAS_AUTHOR_PROPS,
    ),
    "AliasRole": ClassInfo(
        name="AliasRole",
        doc="A Discord role. Returned by `ctx.author.get_roles()`.",
        properties=_ALIAS_ROLE_PROPS,
    ),
    "AliasCategory": ClassInfo(
        name="AliasCategory",
        doc="A Discord channel category. Access via `ctx.channel.category`.",
        properties=_ALIAS_CATEGORY_PROPS,
    ),
    "AliasBaseStats": ClassInfo(
        name="AliasBaseStats",
        doc="Ability scores and proficiency bonus. Access via `character().stats` or `combat().me.stats`.",
        methods=_ALIAS_BASE_STATS_METHODS,
        properties=_ALIAS_BASE_STATS_PROPS,
    ),
    "AliasLevels": ClassInfo(
        name="AliasLevels",
        doc="Class levels for a character. Access via `character().levels`. Use `.get('Fighter')` for a specific class.",
        methods=_ALIAS_LEVELS_METHODS,
        properties=_ALIAS_LEVELS_PROPS,
    ),
    "AliasAttackList": ClassInfo(
        name="AliasAttackList",
        doc="List of attacks for a statblock. Access via `character().attacks`. Iterable and subscriptable.",
        element_type="AliasAttack",
    ),
    "AliasAttack": ClassInfo(
        name="AliasAttack",
        doc="A single attack entry. Yielded when iterating an AliasAttackList.",
        properties=_ALIAS_ATTACK_PROPS,
    ),
    "AliasSkill": ClassInfo(
        name="AliasSkill",
        doc="A single skill or save modifier. Access via `character().skills.athletics` or `character().saves.get('str')`.",
        methods=_ALIAS_SKILL_METHODS,
        properties=_ALIAS_SKILL_PROPS,
    ),
    "AliasSkills": ClassInfo(
        name="AliasSkills",
        doc="Skill modifiers for a statblock. Access via `character().skills`. Subscriptable by skill name (e.g. `.athletics`, `['stealth']`).",
        element_type="AliasSkill",
    ),
    "AliasSaves": ClassInfo(
        name="AliasSaves",
        doc="Saving throw modifiers for a statblock. Access via `character().saves`. Use `.get('str')` to retrieve by ability.",
        methods=[
            _fn("get", "get(base_stat)", "Return the AliasSkill for the given ability save (e.g. 'str', 'dex').", ["base_stat: str"], "AliasSkill"),
        ],
    ),
    "AliasResistances": ClassInfo(
        name="AliasResistances",
        doc="Damage resistances, immunities, and vulnerabilities. Access via `character().resistances`.",
        methods=_ALIAS_RESISTANCES_METHODS,
        properties=_ALIAS_RESISTANCES_PROPS,
    ),
    "AliasSpellbook": ClassInfo(
        name="AliasSpellbook",
        doc="Spellcasting data for a character. Access via `character().spellbook`.",
        methods=_ALIAS_SPELLBOOK_METHODS,
        properties=_ALIAS_SPELLBOOK_PROPS,
    ),
    "AliasSpellbookSpell": ClassInfo(
        name="AliasSpellbookSpell",
        doc="A spell in a character's spellbook. Access via `character().spellbook.spells` or `.find(name)`.",
        properties=_ALIAS_SPELLBOOK_SPELL_PROPS,
    ),
}

BUILTINS: dict[str, BuiltinInfo] = {
    b.name: b for b in _DRACONIC_BUILTINS + _AVRAE_BUILTINS
}


def unwrap_type(type_str: str) -> str:
    """Strip '| None' and unwrap list[X] -> X so list properties chain correctly."""
    t = type_str.split("|")[0].strip()
    if t.startswith("list[") and t.endswith("]"):
        t = t[5:-1]
    return t


def find_member_type(type_name: str, member_name: str) -> str | None:
    """Return the (unwrapped) return_type of a named method/property on `type_name`, following bases."""
    cls_info = CLASS_REGISTRY.get(type_name)
    if cls_info is None:
        return None
    visited: set[str] = set()

    def _search(info: ClassInfo) -> str | None:
        if info.name in visited:
            return None
        visited.add(info.name)
        for m in info.methods + info.properties:
            if m.name == member_name:
                return unwrap_type(m.return_type) if m.return_type else None
        for base_name in info.bases:
            base = CLASS_REGISTRY.get(base_name)
            if base:
                result = _search(base)
                if result is not None:
                    return result
        return None

    return _search(cls_info)
