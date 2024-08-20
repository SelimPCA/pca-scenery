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
