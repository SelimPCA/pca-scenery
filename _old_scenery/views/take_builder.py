# import re

# # from typing import Any

# from app.tests.views.dataclasses import (
#     Case,
#     HttpTake,
#     HttpScene,
#     HttpDirective,
#     HttpCheck,
# )

# # from app.tests.views.enums import HttpTarget

# from django.db.models.base import ModelBase


# class TakeBuilder:

#     regex_field = re.compile(r"^(?P<item_id>[a-z_]+):?(?P<field_name>[a-z_]+)?$")

#     @staticmethod
#     def substitute_from_case(field_repr: str, target: HttpTarget, case: Case):
#         """Perform the substitution for a field that is known to require it"""

#         # print("############", case)

#         if not (re_match := re.match(TakeBuilder.regex_field, field_repr)):
#             raise ValueError(f"Invalid field representation '{field_repr}'")
#         match re_match.groups():
#             case item_id, None:
#                 # There is only a reference to the item
#                 # In this case , we pass all the variables with the dict
#                 return case[item_id][target]
#                 # return getattr(case[item_id], target)
#             case item_id, field_name:
#                 # There is only a reference to the item:field_name
#                 # In this case, we pass only the corresponding value
#                 field_value = case[item_id][target][field_name]
#                 # return {field_name: field_value}
#                 return field_value

#     @staticmethod
#     def substitute_recursively(x, target: HttpTarget, case: Case):
#         """Perform the substitution for a whole target"""

#         match x:
#             case int(n):
#                 return n
#             case str(s):
#                 return s
#             case ModelBase():
#                 return x
#             case HttpDirective(instruction, args):
#                 return HttpCheck(
#                     instruction, TakeBuilder.substitute_recursively(args, target, case)
#                 )
#             case {"__from_case__": str(field_repr)}:
#                 return TakeBuilder.substitute_from_case(field_repr, target, case)
#             case dict(d):
#                 return {
#                     key: TakeBuilder.substitute_recursively(value, target, case)
#                     for key, value in d.items()
#                 }
#             case list(l):
#                 return [
#                     TakeBuilder.substitute_recursively(value, target, case)
#                     for value in l
#                 ]
#             case _:
#                 raise ValueError(
#                     f"Cannot build check dom element from '{x}' ('{type(x)}')"
#                 )

#     @staticmethod
#     def shoot(scene: HttpScene, case: Case) -> HttpTake:

#         take_dict = {
#             "method": scene.method,
#             "url": scene.url,
#             "query_parameters": scene.query_parameters,  # TODO: this will be subsituable
#             "data": TakeBuilder.substitute_recursively(
#                 scene.data, HttpTarget.DATA, case
#             ),
#             "url_parameters": TakeBuilder.substitute_recursively(
#                 scene.url_parameters, HttpTarget.URL_PARAMETERS, case
#             ),
#             "checks": TakeBuilder.substitute_recursively(
#                 scene.directives, HttpTarget.CHECKS, case
#             ),
#         }

#         return HttpTake(**take_dict)


# class TakeBuilder:

#     ##############
#     # SUBSTITUTION
#     ##############

#     # (ex: dijon_carnot:academy)
#     regex_field = re.compile(r"^(?P<item_id>[a-z_]+):?(?P<field_name>[a-z_]+)?$")

#     @staticmethod
#     def _substitute_from_case(
#         case: Case,
#         target: str,
#         field_repr: str,
#         assert_single_field=False,
#         field_value_only=False,
#     ) -> dict:
#         """
#         Return a dict containing the data from `case[target]` corresponding
#         to the description from the `field_repr`
#         Examples:
#             "credentials" -> {"user_email": "mail@example.com", "password":"aed,*a0ed"}
#             "credentials:user_email" -> {"user_email": "mail@example.com"}
#         If field_value_only=True, then only the substitued value is returned
#         (applicable only if the field representation refer to a specific field).
#         Example:
#             "credentials:user_email" -> "mail@example.com"
#         """
#         regex_match = re.match(TakeBuilder.regex_field, field_repr)
#         if regex_match is None:
#             raise ValueError(f"Invalid field representation `{field_repr}`")
#         match regex_match.groups():
#             case item_id, None:
#                 # There is only a reference to the item
#                 # In this case , we pass all the variables with the dict
#                 if assert_single_field:
#                     raise ValueError(
#                         f"The field representation `{field_repr}` does not refer to a single field of the case `{case}`."
#                     )
#                 if field_value_only:
#                     raise ValueError(
#                         f"The field representation `{field_repr}` does not refer to a single field of the case `{case}`, field_value_only cannot be set to False."
#                     )
#                 return case[item_id][target]
#             case item_id, field_name:
#                 # There is only a reference to the item:field_name
#                 # In this case, we pass only the corresponding value
#                 field_value = case[item_id][target][field_name]
#                 if field_value_only:
#                     return field_value
#                 else:
#                     return {field_name: field_value}

#     @staticmethod
#     def build_data(case: Case, scene: HttpScene) -> dict:
#         data = {}
#         for field_repr in scene.data:
#             substitution = TakeBuilder._substitute_from_case(case, "data", field_repr)
#             data.update(substitution)

#         return data

#     @staticmethod
#     def build_url_parameters(case: Case, scene: HttpScene) -> dict:
#         url_parameters = {}
#         for key, val in scene.url_parameters.items():
#             match val:
#                 case str(s):
#                     pass
#                 case int(n):
#                     pass
#                 case {"from_case": field_repr}:
#                     val = TakeBuilder._substitute_from_case(
#                         case,
#                         "url_parameters",
#                         field_repr,
#                         assert_single_field=True,
#                         field_value_only=True,
#                     )
#                 case _:
#                     raise ValueError(
#                         f"Cannot build url parameters from '{val}' ({type(val)})"
#                     )
#             url_parameters[key] = val
#         return url_parameters

#     @staticmethod
#     def _build_check_dom_element(case, val: str | dict):
#         # Submethod of build_checks
#         # TODO: rewrite with SingleKeyDict ?
#         # TODO: use this recursive method in all targets ? at least in build url ?
#         match val:
#             case str(s):
#                 pass
#             case {"from_case": field_repr}:
#                 val = TakeBuilder._substitute_from_case(
#                     case,
#                     "checks",
#                     field_repr,
#                     assert_single_field=True,
#                     field_value_only=True,
#                 )
#             case dict(d):
#                 # Recursive
#                 val = {
#                     x: TakeBuilder._build_check_dom_element(case, y)
#                     for x, y in d.items()
#                 }
#             case list(l):
#                 val = [TakeBuilder._build_check_dom_element(case, e) for e in l]
#             case _:
#                 raise ValueError(
#                     f"Cannot build check dom element from {val} ({type(val)})"
#                 )
#         return val

#     @staticmethod
#     def build_checks(case: Case, scene: HttpScene) -> list[HttpCheck]:
#         checks = []
#         for directive in scene.directives:
#             match directive.instruction:
#                 case (
#                     DirectiveCommand.STATUS_CODE
#                     | DirectiveCommand.REDIRECT_URL
#                     | DirectiveCommand.COUNT_INSTANCES
#                 ):
#                     checks.append(HttpCheck(directive.instruction, directive.args))
#                 case DirectiveCommand.DOM_ELEMENT:
#                     args = {}
#                     for key, val in directive.args.items():
#                         val = TakeBuilder._build_check_dom_element(case, val)
#                         args[key] = val
#                     checks.append(HttpCheck(directive.instruction, args))
#                 case _:
#                     raise ValueError(f"Cannot interpret {directive}.")
#         return checks

#     @staticmethod
#     def shoot(case: Case, scene: HttpScene) -> HttpTake:

#         take_dict = {
#             "method": scene.method,
#             "url": scene.url,
#             "query_parameters": scene.query_parameters,
#             "url_parameters": TakeBuilder.build_url_parameters(case, scene),
#             "data": TakeBuilder.build_data(case, scene),
#             "checks": TakeBuilder.build_checks(case, scene),
#         }

#         return HttpTake(**take_dict)


# OLD BUILD CHECKS DOM ELEMENT


# match key, val:
#     case "find", {"id": {"from_case": field_repr}}:
#         # TODO: ce cas devrait etre bcp plus general
#         val = {
#             "id": TakeBuilder._substitute_from_case(
#                 case,
#                 "checks",
#                 field_repr,
#                 assert_single_field=True,
#                 field_value_only=True,
#             )
#         }
#     case "text", str(s):
#         # TODO: Selim est ok avec le polymorphisme ?
#         pass
#     case "text", {"from_case": field_repr}:
#         val = TakeBuilder._substitute_from_case(
#             case,
#             "checks",
#             field_repr,
#             assert_single_field=True,
#             field_value_only=True,
#         )

#     case "attribute", {
#         "name": attribute_name,
#         "value": {"from_case": field_repr},
#     }:
#         val = {
#             "name": attribute_name,
#             "value": TakeBuilder._substitute_from_case(
#                 case,
#                 "checks",
#                 field_repr,
#                 assert_single_field=True,
#                 field_value_only=True,
#             ),
#         }
#     case _:
#         raise ValueError

# return key, val
