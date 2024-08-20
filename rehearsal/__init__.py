import os
import http
import unittest

import common
import manifest


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


# class TestManifest(unittest.TestCase):

#     def test(self):
#         scene = manifest.HttpScene(
#             "GET",
#             "https://www.example.com",
#             [manifest.HttpDirective(manifest.DirectiveCommand("status_code"), 200)],
#             [],
#             {},
#             {},
#         )
#         scenes = [scene]
#         set_up_test_data = [manifest.SetUpInstruction(manifest.SetUpCommand.RESET_DB)]
#         set_up = [manifest.SetUpInstruction(manifest.SetUpCommand.LOGIN)]
#         cases = [
#             manifest.Case("a", [manifest.Item("item_id", {})]),
#             manifest.Case("b", [manifest.Item("item_id", {})]),
#         ]

#         manifest.Manifest(set_up_test_data, set_up, scenes, cases, "origin")
#         manifest.Manifest.from_formatted_dict(
#             {
#                 manifest.ManifestFormattedDictKeys.SET_UP_TEST_DATA: ["reset_db"],
#                 manifest.ManifestFormattedDictKeys.SET_UP: ["login"],
#                 manifest.ManifestFormattedDictKeys.CASES: {"case_id": {"item_id": {}}},
#                 manifest.ManifestFormattedDictKeys.SCENES: [
#                     {
#                         "method": "GET",
#                         "url": "https://www.example.com",
#                         "data": [],
#                         "url_parameters": {},
#                         "query_parameters": {},
#                         "directives": [{"status_code": 200}],
#                     }
#                 ],
#                 manifest.ManifestFormattedDictKeys.MANIFEST_ORIGIN: "origin",
#             }
#         )


# class TestHttpCheck(unittest.TestCase):

#     def test(self):

#         class NotAModel:
#             pass

#         manifest.HttpCheck(manifest.DirectiveCommand("status_code"), 200)
#         manifest.HttpCheck(
#             manifest.DirectiveCommand("redirect_url"), "https://www.example.com"
#         )
#         manifest.HttpCheck(manifest.DirectiveCommand("dom_element"), {})
#         manifest.HttpCheck(
#             manifest.DirectiveCommand("count_instances"), {"model": Profile, "n": 1}
#         )
#         with self.assertRaises(ValueError):
#             manifest.HttpCheck(manifest.DirectiveCommand("status_code"), "200")
#         with self.assertRaises(ValueError):
#             manifest.HttpCheck(manifest.DirectiveCommand("redirect_url"), 0)
#         with self.assertRaises(ValueError):
#             manifest.HttpCheck(manifest.DirectiveCommand("dom_element"), 0)
#         with self.assertRaises(ValueError):
#             manifest.HttpCheck(
#                 manifest.DirectiveCommand("count_instances"),
#                 {"model": NotAModel, "n": 1},
#             )


# class TestHttpTake(unittest.TestCase):

#     def test(self):
#         take = manifest.HttpTake(
#             "GET",
#             "https://www.example.com",
#             [manifest.HttpDirective(manifest.DirectiveCommand("status_code"), 200)],
#             [],
#             {},
#             {},
#         )
#         self.assertEqual(take.method, http.HTTPMethod.GET)
