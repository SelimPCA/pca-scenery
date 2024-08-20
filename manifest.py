"""Represent all data conveied by the manifest"""

from dataclasses import dataclass, field
import enum
import os
import http
from typing import Any
from urllib.parse import urlparse
import re

from common import read_yaml, SingleKeyDict

from django.apps import apps as django_apps
from django.urls import reverse
from django.utils.http import urlencode
from django.urls.exceptions import NoReverseMatch
from django.db.models.base import ModelBase


####################################
# ENUMS
####################################


####################
# MANIFEST TOP LEVEL
####################


class ManifestFormattedDictKeys(enum.Enum):
    """Used in formated dict, they are exactly contained when passed in Manifest.from_formatted_dict"""

    SET_UP_TEST_DATA = "set_up_test_data"
    SET_UP = "set_up"
    CASES = "cases"
    SCENES = "scenes"
    MANIFEST_ORIGIN = "manifest_origin"


class ManifestDictKeys(enum.Enum):
    """Keys allowed for Manifest.from_dict (and .from_yaml)"""

    SET_UP_TEST_DATA = "set_up_test_data"
    SET_UP = "set_up"
    CASES = "cases"
    SCENES = "scenes"
    MANIFEST_ORIGIN = "manifest_origin"

    CASE = "case"
    SCENE = "scene"


class ManifestYAMLKeys(enum.Enum):
    """Keys allowed for Manifest.from_yaml compared to Manifest.from_dict"""

    SET_UP_TEST_DATA = "set_up_test_data"
    SET_UP = "set_up"
    CASES = "cases"
    SCENES = "scenes"
    MANIFEST_ORIGIN = "manifest_origin"

    CASE = "case"
    SCENE = "scene"

    VARIABLES = "variables"


########
# SET UP
########


class SetUpCommand(enum.Enum):
    """Values allowed in Manifest["set_up"] and Manifest["set_up_test_data"]"""

    RESET_DB = "reset_db"
    CREATE_SUPERUSER = "create_superuser"
    CREATE_TESTUSER = "create_testuser"
    LOGIN = "login"
    LOAD_HIGHSCHOOLS = "load_highschools"
    # LOAD_CONTENT = "load_content"


##############
# SUBSTITUTION
##############


# class HttpTarget(Enum):
#     DATA = "data"
#     CHECKS = "checks"
#     URL_PARAMETERS = "url_parameters"


########
# CHECKS
########


class DirectiveCommand(enum.Enum):
    """Values allowed for Manifest["checks"]"""

    STATUS_CODE = "status_code"
    REDIRECT_URL = "redirect_url"
    COUNT_INSTANCES = "count_instances"
    DOM_ELEMENT = "dom_element"


class DomArgument(enum.Enum):
    """Values allowed for Manifest["checks]["dom_element"]"""

    FIND = "find"
    FIND_ALL = "find_all"
    COUNT = "count"
    SCOPE = "scope"
    TEXT = "text"
    ATTRIBUTE = "attribute"


##########################
# SET UP TEST DATA, SET UP
##########################


@dataclass(frozen=True)
class SetUpInstruction:
    """Store the command and potential arguments for setUpTestData and setUp"""

    command: SetUpCommand
    args: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_object(cls, x):

        match x:
            case str(s):
                cmd_name, args = s, {}
            case dict(d) if len(d) == 1:
                cmd_name, args = SingleKeyDict(d).as_tuple()
            case dict(d):
                raise ValueError(
                    f"`SetUpInstruction` cannot be instantiated from dictionnary of length {len(x)}\n{x}"
                )
            case _:
                raise TypeError(
                    f"`SetUpInstruction` cannot be instantiated from {type(x)}"
                )

        return cls(SetUpCommand(cmd_name), args)


########################
# CASE
########################


# @dataclass(frozen=True)
# class HttpItem:
#     """Store potential information that will be used to build the HttpRequest"""

#     _id: str
#     data: dict[str, int | str] = field(default_factory=dict)
#     checks: dict[str, int | str] = field(default_factory=dict)
#     url_parameters: dict[str, int | str] = field(default_factory=dict)

#     def __getitem__(self, key: HttpTarget):
#         # TODO: do I really need this ?
#         return getattr(self, key.value)

#     @classmethod
#     def from_id_and_dict(cls, item_id, item: dict):
#         item.update({"_id": item_id})
#         return cls(**item)


@dataclass(frozen=True)
class Item:
    """Store potential information that will be used to build the HttpRequest"""

    _id: str
    _dict: dict
    # data: dict[str, int | str] = field(default_factory=dict)
    # checks: dict[str, int | str] = field(default_factory=dict)
    # url_parameters: dict[str, int | str] = field(default_factory=dict)

    def __getitem__(self, key):
        # TODO: do I really need this ?
        return self._dict[key]

    # @classmethod
    # def from_id_and_dict(cls, item_id, item: dict):
    #     item.update({"_id": item_id})
    #     return cls(**item)


@dataclass(frozen=True)
class Case:
    """Store a collection of items"""

    _id: str
    items: dict[str, Item]

    def __getitem__(self, item_id):
        # print(f"Required case[{item_id}] on {self.items}")
        # TODO: do I really need this ?
        return self.items[item_id]

    # @classmethod
    # def from_id_and_dict(cls, case_id: str, items: dict[str, dict]):
    #     items = {
    #         item_id: Item.from_id_and_dict(item_id, item_dict)
    #         for item_id, item_dict in items.items()
    #     }
    #     return cls(case_id, items)

    @classmethod
    def from_id_and_dict(cls, case_id: str, items: dict[str, dict]):
        items = {
            item_id: Item(item_id, item_dict) for item_id, item_dict in items.items()
        }
        return cls(case_id, items)


########################
# SCENES
########################


@dataclass
class Substituable:
    field_repr: re.Match
    # target: HttpTarget

    regex_field = re.compile(r"^(?P<item_id>[a-z_]+):?(?P<field_name>[a-z_]+)?$")

    def __post_init__(self):

        if not (re_match := re.match(self.regex_field, self.field_repr)):
            raise ValueError(f"Invalid field representation '{self.field_repr}'")
        else:
            self.field_repr = re_match

    def shoot(self, case: Case):

        match self.field_repr.groups():
            case item_id, None:
                # There is only a reference to the item
                # In this case , we pass all the variables with the dict
                # return case[item_id][self.target]
                return case[item_id]._dict
            case item_id, field_name:
                # There is only a reference to the item:field_name
                # In this case, we pass only the corresponding value
                # field_value = case[item_id][self.target][field_name]
                field_value = case[item_id][field_name]
                return field_value


@dataclass
class HttpDirective:
    """Store a given check to perform, before the substitution (this is part of a Scene, not a Take)"""

    instruction: DirectiveCommand
    args: Any

    def __post_init__(self):
        """Format self.args"""

        match self.instruction, self.args:
            case DirectiveCommand.STATUS_CODE, int(n):
                self.args = http.HTTPStatus(n)
                # Workaround if we want the class to be frozen
                # object.__setattr__(self, "args", HTTPStatus(n))
                pass
            case DirectiveCommand.STATUS_CODE, Substituable(_):
                # TODO: check single field
                pass
            case DirectiveCommand.DOM_ELEMENT, dict(d):
                self.args = {DomArgument(key): value for key, value in d.items()}
                # Check if there is and only one locator
                locators = [
                    self.args.get(key, None)
                    for key in (DomArgument.FIND_ALL, DomArgument.FIND)
                ]
                if not any(locators):
                    raise ValueError(
                        "Neither `find_all` or `find` provided to check DOM element"
                    )
                else:
                    locators = list(filter(None, locators))
                    if len(locators) > 1:
                        raise ValueError("More than one locator provided")

            case DirectiveCommand.DOM_ELEMENT, Substituable(field_repr, target):
                # TODO
                pass
            case DirectiveCommand.REDIRECT_URL, str(s):
                pass
                # TODO
            case DirectiveCommand.REDIRECT_URL, Substituable(field_repr, target):
                # TODO
                pass
            case DirectiveCommand.COUNT_INSTANCES, {"model": str(s), "n": int(n)}:
                app_config = django_apps.get_app_config(os.getenv("SCENERY_TESTED_APP"))
                self.args["model"] = app_config.get_model(s)
            case DirectiveCommand.COUNT_INSTANCES, Substituable(field_repr, target):
                # TODO
                pass
            case _:
                raise ValueError(
                    f"Cannot interpret '{self.instruction}:({self.args})' as Directive"
                )

    @classmethod
    def from_dict(cls, directive_dict: dict):
        # print("############", directive_dict)
        instruction, args = SingleKeyDict(directive_dict).as_tuple()
        return cls(DirectiveCommand(instruction), args)


@dataclass
class HttpScene:
    """
    Store all actions to perform, before the  of information form the `Cases`.
    """

    method: http.HTTPMethod
    url: str
    directives: list[HttpDirective]
    data: dict[str, Any] = field(default_factory=dict)
    query_parameters: dict = field(default_factory=dict)
    url_parameters: dict = field(default_factory=dict)

    def __post_init__(self):
        self.method = http.HTTPMethod(self.method)
        # At this point we don't check url as we wait for subsitution
        # potentially occuring through data/query_parameters/url_parameters

    @classmethod
    def from_dict(cls, d: dict):
        d["directives"] = [
            HttpDirective.from_dict(directive) for directive in d["directives"]
        ]
        return cls(**d)

    # @classmethod
    # def substitute_recursively(cls, x, target: HttpTarget, case: Case):
    #     """Perform the substitution for a whole target"""

    #     match x:
    #         case int(n):
    #             return n
    #         case str(s):
    #             return s
    #         case ModelBase():
    #             return x
    #         case HttpDirective(instruction, args):
    #             return HttpCheck(
    #                 instruction, cls.substitute_recursively(args, target, case)
    #             )
    #         case Substituable(f):
    #             return x.shoot(case)
    #         case dict(d):
    #             return {
    #                 key: cls.substitute_recursively(value, target, case)
    #                 for key, value in d.items()
    #             }
    #         case list(l):
    #             return [cls.substitute_recursively(value, target, case) for value in l]
    #         case _:
    #             raise NotImplementedError(
    #                 f"Cannot substitute recursively '{x}' ('{type(x)}')"
    #             )

    @classmethod
    def substitute_recursively(cls, x, case: Case):
        """Perform the substitution"""

        match x:
            case int(_) | str(_):
                return x
            case ModelBase():
                return x
            case Substituable(_):
                return x.shoot(case)
            case HttpDirective(instruction, args):
                return HttpCheck(instruction, cls.substitute_recursively(args, case))
            case dict(_):
                return {
                    key: cls.substitute_recursively(value, case)
                    for key, value in x.items()
                }
            case list(_):
                return [cls.substitute_recursively(value, case) for value in x]
            case _:
                raise NotImplementedError(
                    f"Cannot substitute recursively '{x}' ('{type(x)}')"
                )

    def shoot(self, case):

        # TODO: queryparameters substituable?
        # TODO: add headers
        # print("case")
        # print(case)
        # print("data")
        # print(self.data)
        # print("sr data")
        # print(self.substitute_recursively(self.data, case))

        return HttpTake(
            method=self.method,
            url=self.url,
            query_parameters=self.query_parameters,
            data=self.substitute_recursively(self.data, case),
            url_parameters=self.substitute_recursively(self.url_parameters, case),
            checks=self.substitute_recursively(self.directives, case),
        )


################
# MANIFEST
################


@dataclass(frozen=True)
class Manifest:
    """Store all the information to build/shoot all different `Takes`"""

    set_up_test_data: list[SetUpInstruction]
    set_up: list[SetUpInstruction]
    scenes: list[HttpScene]
    cases: dict[str, Case]
    manifest_origin: str

    @classmethod
    def from_formatted_dict(cls, d: dict):
        return cls(
            [
                SetUpInstruction.from_object(instruction)
                for instruction in d[ManifestFormattedDictKeys.SET_UP_TEST_DATA]
            ],
            [
                SetUpInstruction.from_object(instruction)
                for instruction in d[ManifestFormattedDictKeys.SET_UP]
            ],
            [
                HttpScene.from_dict(scene)
                for scene in d[ManifestFormattedDictKeys.SCENES]
            ],
            {
                case_id: Case.from_id_and_dict(case_id, case_dict)
                for case_id, case_dict in d[ManifestFormattedDictKeys.CASES].items()
            },
            d[ManifestFormattedDictKeys.MANIFEST_ORIGIN],
        )


########################
# TAKES
########################


@dataclass
class HttpCheck(HttpDirective):
    """Store a given check to perform (after the subsitution)"""

    def __post_init__(self):
        """Format self.args"""

        match self.instruction, self.args:
            case DirectiveCommand.STATUS_CODE, int(n):
                self.args = http.HTTPStatus(n)
            case DirectiveCommand.DOM_ELEMENT, dict(d):
                self.args = {DomArgument(key): value for key, value in d.items()}
                if attribute := self.args.get(DomArgument.ATTRIBUTE):
                    self.args[DomArgument.ATTRIBUTE]["value"] = (
                        self._format_dom_element_attribute_value(attribute["value"])
                    )
                # TODO: validate value for other cases
            case DirectiveCommand.REDIRECT_URL, str(s):
                pass
                # TODO
            case DirectiveCommand.COUNT_INSTANCES, {"model": ModelBase(), "n": int(n)}:
                # Validate model is registered
                app_config = django_apps.get_app_config(os.getenv("SCENERY_TESTED_APP"))
                app_config.get_model(self.args["model"].__name__)
            case _:
                raise ValueError(
                    f"Cannot interpret '{self.instruction}:({self.args})' as Directive"
                )

    @staticmethod
    def _format_dom_element_attribute_value(value):
        match value:
            case str(s):
                return value
            case list(l):
                return value
            case int(n):
                return str(n)
            case x:
                raise ValueError(
                    f"attribute value can only be `str` or `list[str]` not {x} ('{type(x)}')"
                )


@dataclass
class HttpTake:
    """
    Store all the information, after the subsitution from the `Cases` has been performed
    `url` is expected to be either a valid url or a registered viewname.
    """

    method: http.HTTPMethod
    url: str
    checks: list[HttpCheck]
    data: dict
    query_parameters: dict
    url_parameters: dict

    def __post_init__(self):
        self.method = http.HTTPMethod(self.method)

        try:
            # First we try if the url is a django viewname
            self.url = reverse(self.url, kwargs=self.url_parameters)
        except NoReverseMatch:
            # Otherwise we check it is a valid url
            parsed = urlparse(self.url)
            if not (parsed.scheme and parsed.netloc):
                raise ValueError(
                    f"'{self.url}' could not be reversed and is not a valid url"
                )

        if self.query_parameters:
            # We use http.urlencode instead for compatibility
            # https://stackoverflow.com/questions/4995279/including-a-querystring-in-a-django-core-urlresolvers-reverse-call
            # https://gist.github.com/benbacardi/227f924ec1d9bedd242b
            self.url += "?" + urlencode(self.query_parameters)
