"""General functions and classes used by other modules"""

import dataclasses
import re
import typing

import yaml

########################
# SINGLE KEY DICTIONNARY
########################

# TODO: should this move to manifest ?

SingleKeyDictKey = typing.TypeVar("SingleKeyDictKey", bound=str)
SingleKeyDictKeyValue = typing.TypeVar("SingleKeyDictKeyValue")


@dataclasses.dataclass
class SingleKeyDict(typing.Generic[SingleKeyDictKey, SingleKeyDictKeyValue]):
    """This is mostly useful to have a quick as_tuple representation of a dict {key:value} returned as (key, val)"""

    _dict: typing.Dict[SingleKeyDictKey, SingleKeyDictKeyValue] = dataclasses.field()
    key: SingleKeyDictKey = dataclasses.field(init=False)
    value: SingleKeyDictKeyValue = dataclasses.field(init=False)

    # TODO: it should also be feasible to init with a tuple
    # TODO: and return as a dict

    def __post_init__(self):
        self.validate()
        self.key, self.value = next(iter(self._dict.items()))

    def validate(self):
        if len(self._dict) != 1:
            raise ValueError(
                f"SingleKeyDict should have length 1 not '{len(self._dict)}'\n{self._dict}"
            )

    def as_tuple(self):
        """THIS SHOULD NOT BE CONFUSED WITH BUILT-IN METHOD datclasses.astuple"""
        return self.key, self.value


########
# YAML #
########


def read_yaml(filename: str) -> typing.Any:
    """A function to read a YAML file"""
    with open(filename, "r") as f:
        return yaml.safe_load(f)


#######################
# STRING MANIPULATION #
#######################


def snake_to_camel_case(s: str) -> str:
    """Transforms a string assumed to be in snake_case into CamelCase"""
    if not re.fullmatch(r"[a-z0-9_]+", s):
        raise ValueError(f"'{s}' is not snake_case")
    words = s.split("_")
    camel_case = "".join(word.capitalize() for word in words)
    return camel_case


##############################################
# Ceil and Floor but not external dependencies
##############################################
# NOTE: used below


def floor(n):
    if isinstance(n, int):
        return n
    else:
        return int(n // 1)


def ceil(n):
    if isinstance(n, int):
        return n
    else:
        return int(n // 1) + 1


##################
# TERMINAL OUTPUT
##################

# TODO: this will move

import sys
import os
from contextlib import contextmanager


# @contextmanager
# def redirect_stdout(target=None):
#     # NOTE: written by chatgpt
#     original_stdout = sys.stdout  # Save the reference to the original stdout
#     if target is None:
#         # Open os.devnull if no target specified to suppress all output
#         with open(os.devnull, "w") as nullfile:
#             sys.stdout = nullfile
#             yield
#     else:
#         sys.stdout = target
#         yield
#     sys.stdout = original_stdout  # Restore stdout after exiting the context


class colorize:
    """A context manager for colorizing text in the console"""

    colors = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m",
    }

    def __init__(self, color, text=None):
        if callable(color):
            if text is None:
                raise Exception("Cannot provide a color mapping without text")
            self.color = color(text)

        else:
            self.color = color
        self.text = text

    def __enter__(self):
        print(self.colors[self.color], end="")  # Set the color
        return self  # Return context manager itself if needed

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(self.colors["reset"], end="")  # Reset the color

    def __str__(self):
        if self.text is not None:
            return f"{self.colors[self.color]}{self.text}{self.colors['reset']}"
        else:
            return ""


def tabulate(d: dict, color=None, delim=":"):
    """Return an ascii table for a dict with columns [key, value]"""
    width = max(len(key) for key in d.keys())
    table = [(key, val) for key, val in d.items()]
    if color:
        table = [(key, colorize(color, val)) for key, val in table]
    table = [("\t", key.ljust(width), delim, str(val)) for key, val in table]
    table = ["".join(line) for line in table]
    table = "\n".join(table)
    return table


def graph_bar(d: dict, scale=20):
    """Returns an ascii graph bar (all values between 0 and 1)"""
    # bars = {key: (val, 1 - val) for key, val in d.items()}
    bars = {key: (floor(scale * x), scale - floor(scale * x)) for key, x in d.items()}
    bars = {
        key: str(colorize("green", "=" * x)) + str(colorize("red", "=" * y))
        for key, (x, y) in bars.items()
    }

    bars = {key: bar + f"|{int(100 * d[key])} %" for key, bar in bars.items()}
    # bars = {key: bar.ljust(20) + f"|{round(d[key], 2)}" for key, bar in bars.items()}
    return bars
