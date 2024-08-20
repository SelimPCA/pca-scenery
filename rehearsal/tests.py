"""Testcases"""

import http
import unittest

import common
from http_checker import HttpChecker
import manifest
from manifest_parser import ManifestParser
import rehearsal
from rehearsal.project_django.some_app.models import SomeModel

import django.http

#####################
# COMMON
#####################


class TestSingleKeyDict(unittest.TestCase):

    def test(self):
        d = common.SingleKeyDict({"key": "value"})
        self.assertEqual(d.key, "key")
        self.assertEqual(d.value, "value")
        self.assertEqual(d.as_tuple(), ("key", "value"))
        with self.assertRaisesRegex(
            ValueError, r"^SingleKeyDict should have length 1 not '2'"
        ):
            d = common.SingleKeyDict({"1": None, "2": None})


#####################
# MANIFEST DATCLASSES
#####################


class TestSetUpInstruction(unittest.TestCase):

    def test(self):

        cmd_name = "reset_db"
        cmd = manifest.SetUpCommand.RESET_DB
        args = {"arg": object()}

        with self.subTest("__init__ without args"):
            instruction = manifest.SetUpInstruction(cmd)
            self.assertEqual(instruction.command, cmd)
            self.assertEqual(instruction.args, {})

        with self.subTest("__init__ with args"):
            instruction = manifest.SetUpInstruction(cmd, args)
            self.assertEqual(instruction.command, cmd)
            self.assertEqual(instruction.args, args)

        with self.subTest("from_object"):
            instruction = manifest.SetUpInstruction.from_object(cmd_name)
            self.assertEqual(instruction, manifest.SetUpInstruction(cmd))
            instruction = manifest.SetUpInstruction.from_object({cmd_name: args})
            self.assertEqual(instruction, manifest.SetUpInstruction(cmd, args))


class TestItem(unittest.TestCase):

    def test(self):
        d = {"a": object()}
        item = manifest.Item("id", d)
        self.assertEqual(item._id, "id")
        self.assertEqual(item["a"], d["a"])


class TestCase(unittest.TestCase):

    # TODO: wahou this is an incredibly bad name

    def test(self):

        with self.subTest("__init__"):
            case_a = manifest.Case("id", {"item_id": manifest.Item("item_id", {})})
            self.assertEqual(case_a._id, "id")
            self.assertEqual(case_a.items, {"item_id": manifest.Item("item_id", {})})

        with self.subTest("from_id_and_dict"):
            case_b = manifest.Case.from_id_and_dict("id", {"item_id": {}})
            self.assertEqual(case_a, case_b)


class TestHttpDirective(unittest.TestCase):

    def test(self):
        manifest.HttpDirective(manifest.DirectiveCommand("status_code"), 200)
        manifest.HttpDirective(
            manifest.DirectiveCommand("redirect_url"), "https://www.example.com"
        )
        manifest.HttpDirective(
            manifest.DirectiveCommand("dom_element"), {"find": object()}
        )
        manifest.HttpDirective(
            manifest.DirectiveCommand("count_instances"), {"model": "SomeModel", "n": 1}
        )
        with self.assertRaises(ValueError):
            manifest.HttpDirective(manifest.DirectiveCommand("status_code"), "200")
        with self.assertRaises(ValueError):
            manifest.HttpDirective(manifest.DirectiveCommand("redirect_url"), 0)
        with self.assertRaises(ValueError):
            manifest.HttpDirective(manifest.DirectiveCommand("dom_element"), 0)
        with self.assertRaises(LookupError):
            manifest.HttpDirective(
                manifest.DirectiveCommand("count_instances"),
                {"model": "NotAModel", "n": 1},
            )

        manifest.HttpDirective.from_dict({"dom_element": {"find": object()}})
        manifest.HttpDirective.from_dict(
            {"dom_element": {"find": object(), "scope": {}}}
        )
        manifest.HttpDirective.from_dict({"dom_element": {"find_all": object()}})
        with self.assertRaises(ValueError):
            manifest.HttpDirective.from_dict({"dom_element": {"scope": {}}})
        with self.assertRaises(ValueError):
            manifest.HttpDirective.from_dict(
                {"dom_element": {"find": object(), "find_all": object()}}
            )


class TestSubstituable(unittest.TestCase):

    def test(self):
        case = manifest.Case(
            "id", {"item_id": manifest.Item("item_id", {"a": object()})}
        )
        sub = manifest.Substituable("item_id")
        x = sub.shoot(case)
        self.assertDictEqual(x, case["item_id"]._dict)
        sub = manifest.Substituable("item_id:a")
        x = sub.shoot(case)
        self.assertEqual(x, case["item_id"]["a"])

    def test_regex(self):

        self.assertRegex("item", manifest.Substituable.regex_field)
        self.assertRegex("item_with_underscore", manifest.Substituable.regex_field)
        self.assertRegex("item:field", manifest.Substituable.regex_field)
        self.assertRegex(
            "item:field_with_underscore", manifest.Substituable.regex_field
        )
        self.assertNotRegex("item_Uppercase", manifest.Substituable.regex_field)
        self.assertNotRegex("item_0", manifest.Substituable.regex_field)
        self.assertNotRegex("item-with-hyphen", manifest.Substituable.regex_field)
        self.assertNotRegex("item:field_Uppercase", manifest.Substituable.regex_field)
        self.assertNotRegex("item:field_0", manifest.Substituable.regex_field)
        self.assertNotRegex("item:field-with-hyphen", manifest.Substituable.regex_field)


class TestHttpScene(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.scene_base_dict = {
            "method": "GET",
            "url": "https://www.example.com",
            "directives": [{"status_code": 200}],
        }

        case_dict = {
            "item_id": {
                "a": object(),
                "b": object(),
                "status_code": 200,
                "dom_element_id": "id",
                "attribute_value": "value",
            },
        }

        self.case = manifest.Case.from_id_and_dict("case_id", case_dict)

    def test(self):
        manifest.HttpScene(
            "GET",
            "https://www.example.com",
            [manifest.HttpDirective(manifest.DirectiveCommand("status_code"), 200)],
            [],
            {},
            {},
        )
        manifest.HttpScene.from_dict(
            {
                "method": "GET",
                "url": "https://www.example.com",
                "directives": [{"status_code": 200}],
                "data": [],
                "url_parameters": {},
                "query_parameters": {},
            }
        )

    def test_substitute_recusively(self):

        scene = manifest.HttpScene.from_dict(
            self.scene_base_dict
            | {
                "data": manifest.Substituable("item_id"),
                "url_parameters": manifest.Substituable("item_id"),
                "directives": [
                    {
                        manifest.DirectiveCommand.STATUS_CODE: manifest.Substituable(
                            "item_id:status_code"
                        )
                    }
                ],
            }
        )
        data = manifest.HttpScene.substitute_recursively(scene.data, self.case)
        self.assertDictEqual(data, self.case["item_id"]._dict)
        url_parameters = manifest.HttpScene.substitute_recursively(
            scene.url_parameters, self.case
        )
        self.assertDictEqual(url_parameters, self.case["item_id"]._dict)
        checks = manifest.HttpScene.substitute_recursively(scene.directives, self.case)

        self.assertEqual(
            checks[0],
            manifest.HttpCheck.from_dict(
                {"status_code": self.case["item_id"]["status_code"]}
            ),
        )

    def test_shoot(self):
        scene = manifest.HttpScene.from_dict(
            self.scene_base_dict
            | {"data": {"a": manifest.Substituable("item_id:a")}}
            | {"url_parameters": {"key": manifest.Substituable("item_id:a")}}
            | {
                "directives": [
                    {
                        "dom_element": {
                            "find": {
                                "id": manifest.Substituable("item_id:dom_element_id")
                            },
                            "attribute": {
                                "name": "name",
                                "value": manifest.Substituable(
                                    "item_id:attribute_value"
                                ),
                            },
                        }
                    }
                ]
            }
        )
        take = scene.shoot(self.case)
        self.assertEqual(
            take,
            manifest.HttpTake(
                method=self.scene_base_dict["method"],
                url=self.scene_base_dict["url"],
                data={"a": self.case["item_id"]["a"]},
                url_parameters={"key": self.case["item_id"]["a"]},
                query_parameters={},
                checks=[
                    manifest.HttpCheck(
                        instruction=manifest.DirectiveCommand.DOM_ELEMENT,
                        args={
                            "find": {
                                "id": self.case["item_id"]["dom_element_id"],
                            },
                            "attribute": {
                                "name": "name",
                                "value": self.case["item_id"]["attribute_value"],
                            },
                        },
                    )
                ],
            ),
        )


class TestManifest(unittest.TestCase):

    def test(self):
        scene = manifest.HttpScene(
            "GET",
            "https://www.example.com",
            [manifest.HttpDirective(manifest.DirectiveCommand("status_code"), 200)],
            [],
            {},
            {},
        )
        scenes = [scene]
        set_up_test_data = [manifest.SetUpInstruction(manifest.SetUpCommand.RESET_DB)]
        set_up = [manifest.SetUpInstruction(manifest.SetUpCommand.LOGIN)]
        cases = [
            manifest.Case("a", [manifest.Item("item_id", {})]),
            manifest.Case("b", [manifest.Item("item_id", {})]),
        ]

        manifest.Manifest(set_up_test_data, set_up, scenes, cases, "origin")
        manifest.Manifest.from_formatted_dict(
            {
                manifest.ManifestFormattedDictKeys.SET_UP_TEST_DATA: ["reset_db"],
                manifest.ManifestFormattedDictKeys.SET_UP: ["login"],
                manifest.ManifestFormattedDictKeys.CASES: {"case_id": {"item_id": {}}},
                manifest.ManifestFormattedDictKeys.SCENES: [
                    {
                        "method": "GET",
                        "url": "https://www.example.com",
                        "data": [],
                        "url_parameters": {},
                        "query_parameters": {},
                        "directives": [{"status_code": 200}],
                    }
                ],
                manifest.ManifestFormattedDictKeys.MANIFEST_ORIGIN: "origin",
            }
        )


class TestHttpCheck(unittest.TestCase):

    def test(self):

        class NotAModel:
            pass

        manifest.HttpCheck(manifest.DirectiveCommand("status_code"), 200)
        manifest.HttpCheck(
            manifest.DirectiveCommand("redirect_url"), "https://www.example.com"
        )
        manifest.HttpCheck(manifest.DirectiveCommand("dom_element"), {})
        manifest.HttpCheck(
            manifest.DirectiveCommand("count_instances"), {"model": SomeModel, "n": 1}
        )
        with self.assertRaises(ValueError):
            manifest.HttpCheck(manifest.DirectiveCommand("status_code"), "200")
        with self.assertRaises(ValueError):
            manifest.HttpCheck(manifest.DirectiveCommand("redirect_url"), 0)
        with self.assertRaises(ValueError):
            manifest.HttpCheck(manifest.DirectiveCommand("dom_element"), 0)
        with self.assertRaises(ValueError):
            manifest.HttpCheck(
                manifest.DirectiveCommand("count_instances"),
                {"model": NotAModel, "n": 1},
            )


class TestHttpTake(unittest.TestCase):

    def test(self):
        take = manifest.HttpTake(
            "GET",
            "https://www.example.com",
            [manifest.HttpDirective(manifest.DirectiveCommand("status_code"), 200)],
            [],
            {},
            {},
        )
        self.assertEqual(take.method, http.HTTPMethod.GET)


#################
# MANIFEST PARSER
#################


class TestManifestParser(unittest.TestCase):

    def test_parse_formatted_dict(self):
        d = {
            "set_up_test_data": [],
            "set_up": [],
            "cases": {},
            "scenes": [],
            "manifest_origin": "origin",
        }
        ManifestParser.parse_formatted_dict(d)
        d.pop("cases")
        with self.assertRaises(KeyError):
            ManifestParser.parse_formatted_dict(d)

    def test_validate_dict(self):
        manifest_base_dict = {
            "set_up_test_data": object(),
            "set_up": object(),
            "cases": object(),
            "scenes": object(),
            "manifest_origin": "origin",
        }

        # Unknown key
        manifest = manifest_base_dict | {"unknown": object()}
        with self.assertRaises(ValueError):

            ManifestParser.validate_dict(manifest)

        # Both case and cases
        manifest = manifest_base_dict | {"case": object()}
        with self.assertRaisesRegex(
            ValueError,
            r"Both `case` and `cases` keys are present at top level\.$",
        ):
            ManifestParser.validate_dict(manifest)

        # Neither case or cases
        manifest = manifest_base_dict.copy()
        manifest.pop("cases")
        with self.assertRaisesRegex(
            ValueError,
            r"Neither `case` and `cases` keys are present at top level\.$",
        ):
            ManifestParser.validate_dict(manifest)

        # Both scene and scenes
        manifest = manifest_base_dict | {"scene": object()}
        with self.assertRaisesRegex(
            ValueError,
            r"Both `scene` and `scenes` keys are present at top level\.$",
        ):
            ManifestParser.validate_dict(manifest)

        # Neither scene or scenes
        manifest = manifest_base_dict.copy()
        manifest.pop("scenes")
        with self.assertRaisesRegex(
            ValueError,
            r"Neither `scene` and `scenes` keys are present at top level\.$",
        ):
            ManifestParser.validate_dict(manifest)

        # Success all fields
        manifest = manifest_base_dict
        ManifestParser.validate_dict(manifest)

        # Success no optional field
        manifest = manifest_base_dict.copy()
        manifest.pop("set_up")
        manifest.pop("set_up_test_data")
        ManifestParser.validate_dict(manifest)

    def test_format_dict(self):
        scene_1 = object()
        scene_2 = object()
        case_1 = object()
        case_2 = object()
        manifest = {
            "cases": [case_1, case_2],
            "scenes": [scene_1, scene_2],
            "manifest_origin": "origin",
        }
        ManifestParser.validate_dict(manifest)
        manifest = ManifestParser.format_dict(manifest)
        self.assertDictEqual(
            manifest,
            {
                "cases": [case_1, case_2],
                "scenes": [scene_1, scene_2],
                "manifest_origin": "origin",
                "set_up_test_data": [],
                "set_up": [],
            },
        )
        manifest = {
            "case": case_1,
            "scene": scene_1,
            "manifest_origin": "origin",
            "set_up_test_data": ["a", "b"],
            "set_up": ["c", "d"],
        }
        ManifestParser.validate_dict(manifest)
        manifest = ManifestParser.format_dict(manifest)
        self.assertDictEqual(
            manifest,
            {
                "cases": {"UNIQUE_CASE": case_1},
                "scenes": [scene_1],
                "manifest_origin": "origin",
                "set_up_test_data": ["a", "b"],
                "set_up": ["c", "d"],
            },
        )

    def test__format_dict_scenes(self):

        scene_1 = object()
        scene_2 = object()
        manifest_base_dict = {
            "cases": object(),
            "manifest_origin": "origin",
        }

        # Single scene
        manifest = manifest_base_dict | {"scene": scene_1}
        ManifestParser.validate_dict(manifest)
        scenes = ManifestParser._format_dict_scenes(manifest)
        self.assertListEqual(scenes, [scene_1])

        # Single scene in scenes
        manifest = manifest_base_dict | {"scenes": [scene_1]}
        ManifestParser.validate_dict(manifest)
        scenes = ManifestParser._format_dict_scenes(manifest)
        self.assertListEqual(scenes, [scene_1])

        # Scenes
        manifest = manifest_base_dict | {"scenes": [scene_1, scene_2]}
        ManifestParser.validate_dict(manifest)
        scenes = ManifestParser._format_dict_scenes(manifest)
        self.assertListEqual(scenes, [scene_1, scene_2])

    def test__format_dict_cases(self):

        case_1 = object()
        case_2 = object()
        manifest_base_dict = {
            "scenes": object(),
            "manifest_origin": "origin",
        }

        # Single case
        manifest = manifest_base_dict | {"case": case_1}
        ManifestParser.validate_dict(manifest)
        cases = ManifestParser._format_dict_cases(manifest)
        self.assertDictEqual(cases, {"UNIQUE_CASE": case_1})

        # Single case in cases
        manifest = manifest_base_dict | {"cases": {"case_id": case_1}}
        ManifestParser.validate_yaml(manifest)
        cases = ManifestParser._format_dict_cases(manifest)
        self.assertDictEqual(cases, {"case_id": case_1})

        # Cases
        manifest = manifest_base_dict | {"cases": {"case_1": case_1, "case_2": case_2}}
        ManifestParser.validate_dict(manifest)
        cases = ManifestParser._format_dict_cases(manifest)
        self.assertDictEqual(cases, {"case_1": case_1, "case_2": case_2})

    def test_parse_dict(self):
        d = {
            "case": {},
            "scene": {
                "method": "GET",
                "url": "https://www.example.com",
                "directives": [{"status_code": 200}],
            },
            "manifest_origin": "origin",
            "set_up_test_data": ["reset_db"],
            "set_up": ["create_testuser"],
        }
        ManifestParser.parse_dict(d)
        d.pop("case")
        with self.assertRaises(ValueError):
            ManifestParser.parse_dict(d)

    def test_validate_yaml(self):

        # wrong type
        manifest = []
        with self.assertRaisesRegex(
            TypeError, r"^Manifest need to be a dict not a '<class 'list'>'$"
        ):
            ManifestParser.validate_yaml(manifest)

        # success
        manifest = {
            "variables": object(),
            "cases": object(),
            "scenes": object(),
            "manifest_origin": "origin",
        }
        ManifestParser.validate_yaml(manifest)


#################
# HTTP CHECKER
#################

class TestHttpChecker(rehearsal.TestCaseOfDjangoTestCase):

    def test_check_status_code(self):

        response = django.http.HttpResponse()
        response.status_code = 200

        def test_pass(django_testcase):
            HttpChecker.check_status_code(django_testcase, response, 200)

        def test_fail(django_testcase):
            HttpChecker.check_status_code(django_testcase, response, 400)

        self.django_testcase.test_pass = test_pass
        self.django_testcase.test_fail = test_fail

        self.assertTestPasses(self.django_testcase("test_pass"))
        self.assertTestFails(self.django_testcase("test_fail"))

    def test_check_redirect_url(self):
        response = django.http.HttpResponseRedirect(redirect_to="somewhere")

        def test_pass(django_testcase):
            HttpChecker.check_redirect_url(django_testcase, response, "somewhere")

        def test_fail(django_testcase):
            HttpChecker.check_redirect_url(django_testcase, response, "elsewhere")

        self.django_testcase.test_pass = test_pass
        self.django_testcase.test_fail = test_fail

        self.assertTestPasses(self.django_testcase("test_pass"))
        self.assertTestFails(self.django_testcase("test_fail"))

    def test_check_count_instances(self):
        SetUpHandler.reset_db()  # As is it tested in TestSetUpInstructions we assume it is working
        response = django.http.HttpResponse()

        def test_pass(django_testcase):
            HttpChecker.check_count_instances(
                django_testcase, response, {"model": SomeModel, "n": 0}
            )

        def test_fail(django_testcase):
            HttpChecker.check_count_instances(
                django_testcase, response, {"model": SomeModel, "n": 1}
            )

        # def test_error(django_testcase):
        #     class UndefinedModel:
        #         pass

        #     HttpChecker.check_count_instances(
        #         django_testcase, response, {"model": UndefinedModel, "n": 0}
        #     )

        self.django_testcase.test_pass = test_pass
        self.django_testcase.test_fail = test_fail
        # self.django_testcase.test_error = test_error

        self.assertTestPasses(self.django_testcase("test_pass"))
        self.assertTestFails(self.django_testcase("test_fail"))
        # This actually raises an AttributeError as now data validation is
        # Performed by the HttpTake dataclasses
        # self.assertTestRaises(self.django_testcase("test_error"), LookupError)

    def test_check_dom_element(self):

        def test_pass_find_by_id(django_testcase):
            response = django.http.HttpResponse()
            response.content = '<div id="target">Pass</div>'
            HttpChecker.check_dom_element(
                django_testcase, response, {manifest.DomArgument.FIND: {"id": "target"}}
            )

        def test_pass_find_by_class(django_testcase):
            response = django.http.HttpResponse()
            response.content = '<div class="target">Pass</div>'
            HttpChecker.check_dom_element(
                django_testcase, response, {manifest.DomArgument.FIND: {"class": "target"}}
            )

        def test_pass_text(django_testcase):
            response = django.http.HttpResponse()
            response.content = '<div id="target">Pass</div>'
            HttpChecker.check_dom_element(
                django_testcase,
                response,
                {manifest.DomArgument.FIND: {"id": "target"}, manifest.DomArgument.TEXT: "Pass"},
            )

        def test_pass_attribute(django_testcase):
            response = django.http.HttpResponse()
            response.content = '<div id="target" class="something">Pass</div>'
            HttpChecker.check_dom_element(
                django_testcase,
                response,
                {
                    manifest.DomArgument.FIND: {"id": "target"},
                    manifest.DomArgument.ATTRIBUTE: {"name": "class", "value": ["something"]},
                },
            )

        def test_pass_find_all(django_testcase):
            response = django.http.HttpResponse()
            response.content = (
                '<div class="something">Pass</div> <div class="something">Pass</div>'
            )
            HttpChecker.check_dom_element(
                django_testcase,
                response,
                {
                    manifest.DomArgument.FIND_ALL: {"class": "something"},
                    manifest.DomArgument.COUNT: 2,
                },
            )

        def test_pass_scope(django_testcase):
            response = django.http.HttpResponse()
            response.content = '<div id="scope"> <div class="something">In</div> <div class="something">In</div> </div> <div class="something">'
            HttpChecker.check_dom_element(
                django_testcase,
                response,
                {
                    manifest.DomArgument.SCOPE: {"id": "scope"},
                    manifest.DomArgument.FIND_ALL: {"class": "something"},
                    manifest.DomArgument.COUNT: 2,
                },
            )

        def test_fail_1(django_testcase):
            response = django.http.HttpResponse()
            response.content = '<div id="target">Pass</div>'
            HttpChecker.check_dom_element(
                django_testcase, response, {manifest.DomArgument.FIND: {"id": "another_target"}}
            )

        def test_fail_2(django_testcase):
            response = django.http.HttpResponse()
            response.content = '<div id="target">Pass</div>'
            HttpChecker.check_dom_element(
                django_testcase,
                response,
                {manifest.DomArgument.FIND: {"id": "target"}, manifest.DomArgument.TEXT: "Fail"},
            )

        def test_fail_3(django_testcase):
            response = django.http.HttpResponse()
            response.content = '<div id="target" class="something">Pass</div>'
            HttpChecker.check_dom_element(
                django_testcase,
                response,
                {
                    manifest.DomArgument.FIND: {"id": "target"},
                    manifest.DomArgument.ATTRIBUTE: {
                        "name": "class",
                        "value": ["something_else"],
                    },
                },
            )

        def test_error_1(django_testcase):
            response = django.http.HttpResponse()
            response.content = '<div id="target" class="something">Pass</div>'
            HttpChecker.check_dom_element(
                django_testcase,
                response,
                {},
            )

        self.django_testcase.test_pass_find_by_id = test_pass_find_by_id
        self.django_testcase.test_pass_find_by_class = test_pass_find_by_class
        self.django_testcase.test_pass_text = test_pass_text
        self.django_testcase.test_pass_attribute = test_pass_attribute
        self.django_testcase.test_pass_find_all = test_pass_find_all
        self.django_testcase.test_pass_scope = test_pass_scope
        self.django_testcase.test_fail_1 = test_fail_1
        self.django_testcase.test_fail_2 = test_fail_2
        self.django_testcase.test_fail_3 = test_fail_3
        self.django_testcase.test_error_1 = test_error_1

        self.assertTestPasses(self.django_testcase("test_pass_find_by_id"))
        self.assertTestPasses(self.django_testcase("test_pass_find_by_class"))
        self.assertTestPasses(self.django_testcase("test_pass_attribute"))
        self.assertTestPasses(self.django_testcase("test_pass_text"))
        self.assertTestPasses(self.django_testcase("test_pass_find_all"))
        self.assertTestPasses(self.django_testcase("test_pass_scope"))
        self.assertTestFails(self.django_testcase("test_fail_1"))
        self.assertTestFails(self.django_testcase("test_fail_2"))
        self.assertTestFails(self.django_testcase("test_fail_3"))
        self.assertTestRaises(self.django_testcase("test_error_1"), ValueError)

