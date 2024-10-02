import datetime
import json
import logging

logging.disable(logging.ERROR)

from django.test import TestCase
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict

from django.shortcuts import get_object_or_404

# Data Loaders
from app.management.commands.old___load_content_custom import (
    Command as LoadContentCommand,
)

from app.management.commands.createsuperusercustom import (
    Command as CreateSuperUserCustomCommand,
    EMAIL_SUPERUSER,
    PASSWORD_SUPERUSER,
)

# For mock user creation
from app.models.accounts.user_custom import UserCustom

from app.serializers.listener.user_answer_maths import serialize_user_answer_maths


from app.teachers.emojy import replace_numbers_and_symbols_with_emojis_augmented


from app.serializers.content.block import add_pos_to_choices

from app.teachers.select.select_teacher import SelectTeacher

# Models
from app.models import Fragment

from pprint import pprint


EMAIL = "selim@pointcarre.app"

PASSWORD = "OlO4mR49i2ZkH4Ya2JS8"


class UserAnswerViewTest(TestCase):
    # Only once
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    # Only once ? see below
    @classmethod
    def setUpTestData(cls):
        # https://stackoverflow.com/questions/43594519/what-are-the-differences-between-setupclass-setuptestdata-and-setup-in-testcase
        # Technically only once and db go back to the state
        # at the end by itself (postgres ? support transactionnal?)
        load_content_c = LoadContentCommand()
        load_content_c.handle_test()

        csucc = CreateSuperUserCustomCommand()
        csucc.handle()

        cls.USER = UserCustom.objects.filter(username=EMAIL_SUPERUSER).first()

        cls.input_latex_types = [
            "perfect",
            "correct_not_ordered",
            "correct_not_computed",
            "not_correct",
        ]

    def setUp(self):
        self.client.login(username=EMAIL_SUPERUSER, password=PASSWORD_SUPERUSER)

    def send_user_answer_maths(self, fragment, input_latex_type):
        latex = (
            fragment.get("data", {})
            .get("answer", {})
            .get("value", {})
            .get("tests", {})
            .get("parser-latex", {})
            .get("input-latex", {})
            .get(input_latex_type, "")
        )
        test_data = {
            "user_id": UserAnswerViewTest.USER.id,
            "fragment_id": fragment["id"],
            "landed_at_utc": datetime.datetime.now().isoformat() + "Z",
            "landed_at_local": datetime.datetime.now().isoformat(),
            "clicked_at_utc": (
                datetime.datetime.now() + datetime.timedelta(minutes=1)
            ).isoformat()
            + "Z",
            "user_answer_latex": latex,
            "keyboard_mode": "normal",
        }
        # print(latex)

        response = self.client.post(
            reverse(
                "app:user_answer_maths",
            ),
            json.dumps(test_data, cls=DjangoJSONEncoder),  # for uuid
            content_type="application/json",
        )

        data_for_front = json.loads(response.content)

        return data_for_front

    ##########################################################
    ##########################################################
    ## Test all interactions maths
    ##########################################################
    ##########################################################

    def test_all_interactions_maths(self):
        """Test a POST for user_answer for all (interaction, input_latex_type in test)."""
        for fragment in Fragment.objects.filter(f_type="interaction-maths"):
            self._test_interaction_maths(fragment)
            # print("\n\n\n")

    def _test_interaction_maths(self, fragment):
        fragment = model_to_dict(fragment)

        input_latex_types = (
            fragment.get("data", {})
            .get("answer", {})
            .get("value", {})
            .get("tests", {})
            .get("parser-latex", {})
            .get("input-latex", {})
            .keys()
        )
        for input_latex_type in input_latex_types:
            # print("#######################################", input_latex_type})

            data_for_front = self.send_user_answer_maths(
                fragment, input_latex_type=input_latex_type
            )

            is_correct = data_for_front["is_correct"]
            is_correct_latex = data_for_front["is_correct_latex"]

            self.assertIsCorrect(input_latex_type, is_correct)
            self.assertIsCorrectLatex(input_latex_type, is_correct_latex)
            # print("\n")

        # Test mode too
        # test input of wrong type

    def assertIsCorrect(self, input_latex_type, is_correct):
        if input_latex_type in [
            "perfect",
            "correct_not_ordered",
            "correct_not_computed",
        ]:
            self.assertTrue(is_correct)
        elif input_latex_type in ["not_correct", "not_correct_even_type"]:
            self.assertFalse(is_correct)

        else:
            raise NotImplementedError(f"{input_latex_type} not implemented")

    def assertIsCorrectLatex(self, input_latex_type, is_correct_latex):
        if input_latex_type == "perfect":
            self.assertTrue(is_correct_latex)
        elif input_latex_type in [
            "correct_not_ordered",
            "correct_not_computed",
            "not_correct",
            "not_correct_even_type",
        ]:
            self.assertFalse(is_correct_latex)

        else:
            raise NotImplementedError(f"{input_latex_type} not implemented")

    ##########################################################
    ##########################################################
    ## Test Modes for User Answers Maths
    ##########################################################
    ##########################################################

    def _test_scenario_maths(self, fragment, test_grid):
        for try_ in test_grid:
            input_latex_type = try_[0]
            target_is_correct = try_[1]
            target_is_correct_latex = try_[2]
            target_nth_tentative = try_[3]
            target_saved = try_[5]

            data_for_front = self.send_user_answer_maths(fragment, input_latex_type)
            is_correct = data_for_front["is_correct"]
            is_correct_latex = data_for_front["is_correct_latex"]
            nth_tentative = data_for_front["nth_tentative"]
            saved = data_for_front["saved"]

            self.assertEqual(is_correct, target_is_correct),
            self.assertEqual(is_correct_latex, target_is_correct_latex)
            self.assertEqual(nth_tentative, target_nth_tentative)
            self.assertEqual(saved, target_saved)

    def test_scenario_1_maths(self):
        fragment_slug = "chapitre-tests$notion-etienne$serie-etienne$derivation-13$2"
        fragment = Fragment.objects.filter(slug=fragment_slug).first()
        fragment = model_to_dict(fragment)

        test_grid = [
            # input_latex_type, is_correct, is_correct_latex,
            # nth_tentative,  keyboard_mode, saved
            ("not_correct", False, False, 1, "normal", True),
            ("not_correct", False, False, 2, "normal", True),
            ("not_correct", False, False, 3, "emojy", True),
            ("not_correct", False, False, 4, "emojy", True),
            ("not_correct", False, False, 5, "emojy", True),
            ("not_correct", False, False, 6, "deactivate", True),
            ("not_correct", False, False, 6, "deactivate", False),
            ("not_correct", False, False, 6, "deactivate", False),  # shouldnt be saved
        ]

        self._test_scenario_maths(fragment, test_grid)

    def test_scenario_2_maths(self):
        fragment_slug = "chapitre-tests$notion-etienne$serie-etienne$derivation-13$2"
        fragment = Fragment.objects.filter(slug=fragment_slug).first()
        fragment = model_to_dict(fragment)

        test_grid = [
            ("not_correct", False, False, 1, "normal", True),
            ("correct_not_ordered", True, False, 2, "emojy", True),
            ("not_correct", False, False, 3, "emojy", True),
            ("not_correct", False, False, 4, "emojy", True),
            ("not_correct", False, False, 5, "emojy", True),
            ("perfect", True, True, 6, "deactivate", True),
        ]

        self._test_scenario_maths(fragment, test_grid)

    def test_scenario_3_maths(self):
        fragment_slug = "chapitre-tests$notion-etienne$serie-etienne$derivation-13$2"
        fragment = Fragment.objects.filter(slug=fragment_slug).first()
        fragment = model_to_dict(fragment)

        test_grid = [
            ("perfect", True, True, 1, "deactivate", True),  # the only one saved
            ("correct_not_ordered", True, False, 2, "deactivate", True),
            ("not_correct", False, False, 3, "deactivate", True),
            ("not_correct", False, False, 4, "deactivate", True),
            ("not_correct", False, False, 5, "deactivate", True),
            ("perfect", True, True, 6, "deactivate", True),
            ("perfect", True, True, 6, "deactivate", False),
        ]

        self._test_scenario_maths(fragment, test_grid)

    def test_scenario_4_maths(self):
        fragment_slug = "chapitre-tests$notion-etienne$serie-etienne$derivation-13$2"
        fragment = Fragment.objects.filter(slug=fragment_slug).first()
        fragment = model_to_dict(fragment)

        test_grid = [
            ("not_correct", False, False, 1, "normal", True),
            ("not_correct", False, False, 2, "normal", True),
            ("not_correct", False, False, 3, "emojy", True),
            ("correct_not_computed", True, False, 4, "emojy", True),
            ("perfect", True, True, 5, "deactivate", True),
            ("perfect", True, True, 6, "deactivate", True),
            ("perfect", True, True, 6, "deactivate", False),  # not saved
        ]

        self._test_scenario_maths(fragment, test_grid)

    def test_emojy_mode(self):
        from app.teachers.parsers.parser_latex import ParserLatex
        from app.teachers.parsers.parser_formal import ParserFormal

        self.parser_latex = ParserLatex(universe=None)

        # Test with your example expressions
        expressions = [
            (r"10x-22", "compute_value"),
            (r"(a+b+3)**2", "compute_value"),
            (r"\frac{a+b}{\sqrt{10x-2}}", "compute_value"),
            (r"\cos(x+10+o)", "compute_value"),
            (r"\frac{\cos(x + y)}{\sqrt{a + b}}", "compute_value"),
            (r"\tan(\sin(x + y))", "compute_value"),
            (r"\sqrt{x + y} + \frac{a}{b}", "compute_value"),
            (r"\sin(\frac{x + y}{2})", "compute_value"),
            (r"\frac{1}{\frac{a + b}{c}}", "compute_value"),
            (r"\cos(x) + \cos(y) + \cos(z)", "compute_value"),
            (r"10xacd+y-24+3", "compute_value"),
            ("\\{a,b,c\\}", "compute_set"),
            ("\{10c,\\frac{12}{b},a\}", "compute_set"),
            ("\\{c,b,a+2\\}", "compute_set"),
            ("\\llbracket0,90\\rrbracket", "compute_inequality"),
            (
                "\\llbracket 0,89\\rrbracket\\cup\\llbracket 89,90\\rrbracket",
                "compute_inequality",
            ),
            ("[0, 91]", "compute_inequality"),
            ("]0,+\\inf[", "compute_inequality"),
            ("[0,+\\inf[", "compute_inequality"),
            ("]0,\\inf[", "compute_inequality"),
            ("[0,-\\inf[", "compute_inequality"),
            ("]0,\\inf[", "compute_inequality"),
            ("[-\\inf,+\\inf[", "compute_inequality"),
            ("\\{- 1/3 -\\sqrt{10}/3,  -1/3 +\\sqrt{10}/3\\}", "compute_set"),
            ("\\frac{2h+h^2}{h}", "compute_value"),
            ("\\frac{2ah+h^2}{h}", "compute_value"),
            ("(x, x^2 + 3)", "compute_value"),
            ("(x, 3 + x^2)", "compute_value"),
            ("(x, x^2 + 4 - 1)", "compute_value"),
            ("(3, x)", "compute_value"),
            ("(3, 2, -3)", "compute_value"),
            ("(4, 2, -3)", "compute_value"),
            ("(\\cos(x)^{-2}, \\cos(x))", "compute_value"),
            ("(\\tan(x)^2 + 1, \\cos(x))", "compute_value"),
            ("(1 + \\tan(x)\\tan(x), \\cos(x))", "compute_value"),
            ("(\\tan(x)^2, \\cos(x))", "compute_value"),
            ("]-\\inf,-1[\\cup]1,+\\inf[", "compute_set"),
            ("z(2)", "give_formula"),
        ]

        for latex, nature in expressions:
            expr_sy = self.parser_latex.parse(latex, nature)
            (
                masked_expr,
                emojies_token_types,
                emojis,
            ) = replace_numbers_and_symbols_with_emojis_augmented(latex, expr_sy)
            print(expr_sy, masked_expr)

            # print(latex, masked_expr, "\n")

        # for expr in expressions:
        #     masked_expr = replace_numbers_and_symbols_with_emojis(expr)
        #     print(f"Original expression: {expr}")
        #     print(f"Masked expression: {masked_expr}")
        #     print()

    # ##########################################################
    # ##########################################################
    # ## Test all interactions select
    # ##########################################################
    # ##########################################################

    def send_user_answer_select(self, fragment, pos_list):
        test_data = {
            "user_id": UserAnswerViewTest.USER.id,
            "fragment_id": fragment["id"],
            "landed_at_utc": datetime.datetime.now().isoformat() + "Z",
            "landed_at_local": datetime.datetime.now().isoformat() + "Z",
            "clicked_at_utc": (
                datetime.datetime.now() + datetime.timedelta(minutes=1)
            ).isoformat()
            + "Z",
            "user_answer_pos_list": pos_list,
        }
        # print(latex)

        response = self.client.post(
            reverse(
                "app:user_answer_select",
            ),
            json.dumps(test_data, cls=DjangoJSONEncoder),  # for uuid
            content_type="application/json",
        )

        data_for_front = json.loads(response.content)

        return data_for_front

    def test_all_interactions_select(self):
        """Test a POST"""
        for fragment in Fragment.objects.filter(f_type="interaction-select"):
            self._test_interaction_select(fragment)
            # pass

    def _test_interaction_select(self, fragment):
        fragment = model_to_dict(fragment)

        # Prepare the correct and not correct pos
        choices = fragment["data"]["answer"]["value"]["choices"]
        answer_with_pos = add_pos_to_choices(choices, keep_is_correct=True)
        pos_correct = [x["pos"] for x in answer_with_pos if x["is_correct"]]
        pos_not_correct = [x["pos"] for x in answer_with_pos if not x["is_correct"]]

        ###############################################
        # Test with all the correct
        ###############################################
        print("#######################################", "All correct")
        pos_list = pos_correct
        data_for_front = self.send_user_answer_select(fragment, pos_list)

        is_correct = data_for_front["is_correct"]
        self.assertTrue(is_correct)

        ###############################################
        # Test with empty
        ###############################################
        print("#######################################", "Empty")
        pos_list = []
        data_for_front = self.send_user_answer_select(fragment, pos_list)

        is_correct = data_for_front["is_correct"]
        self.assertFalse(is_correct)

        ###############################################
        # Test with all the not correct
        ###############################################
        print("#######################################", "All not correct")
        pos_list = pos_not_correct
        data_for_front = self.send_user_answer_select(fragment, pos_list)

        is_correct = data_for_front["is_correct"]
        self.assertFalse(is_correct)

        ###############################################
        # Test with all of them
        ###############################################
        print("#######################################", "Mix of correct and uncorrect")
        pos_list = pos_correct + pos_not_correct
        data_for_front = self.send_user_answer_select(fragment, pos_list=pos_list)

        is_correct = data_for_front["is_correct"]
        self.assertFalse(is_correct)

        ###############################################
        # Test with a mix of them
        ###############################################
        print(
            "#######################################",
            "first correct and first uncorrect",
        )
        pos_list = [pos_correct[0], pos_not_correct[0]]
        data_for_front = self.send_user_answer_select(fragment, pos_list=pos_list)

        is_correct = data_for_front["is_correct"]
        self.assertFalse(is_correct)

    def _test_scenario_select(self, fragment, test_grid):
        for try_ in test_grid:
            user_pos_list = try_[0]
            target_is_correct = try_[1]
            target_nth_tentative = try_[2]
            target_select_mode = try_[3]
            target_saved = try_[4]

            data_for_front = self.send_user_answer_select(
                fragment, pos_list=user_pos_list
            )
            is_correct = data_for_front["is_correct"]
            nth_tentative = data_for_front["nth_tentative"]
            select_mode = data_for_front["select_mode"]
            saved = data_for_front["saved"]

            self.assertEqual(is_correct, target_is_correct),
            self.assertEqual(nth_tentative, target_nth_tentative)
            self.assertEqual(select_mode, target_select_mode)
            self.assertEqual(saved, target_saved)

    def test_scenario_1_select(self):
        fragment_slug = (
            "chapitre-tests$notion-fragments$serie-all-fragments$tous-les-fragments$17"
        )
        fragment = Fragment.objects.filter(slug=fragment_slug).first()
        fragment = model_to_dict(fragment)

        # Prepare the correct and not correct pos
        choices = fragment["data"]["answer"]["value"]["choices"]
        answer_with_pos = add_pos_to_choices(choices, keep_is_correct=True)
        pos_correct = [x["pos"] for x in answer_with_pos if x["is_correct"]]
        pos_not_correct = [x["pos"] for x in answer_with_pos if not x["is_correct"]]

        test_grid = [
            (pos_correct, True, 1, "deactivate", True),
            (pos_not_correct, False, 1, "deactivate", False),
            (pos_not_correct, False, 1, "deactivate", False),
        ]

        self._test_scenario_select(fragment, test_grid)

    def test_scenario_2_select(self):
        fragment_slug = (
            "chapitre-tests$notion-fragments$serie-all-fragments$tous-les-fragments$17"
        )
        fragment = Fragment.objects.filter(slug=fragment_slug).first()
        fragment = model_to_dict(fragment)

        # Prepare the correct and not correct pos
        choices = fragment["data"]["answer"]["value"]["choices"]
        answer_with_pos = add_pos_to_choices(choices, keep_is_correct=True)
        pos_correct = [x["pos"] for x in answer_with_pos if x["is_correct"]]
        pos_not_correct = [x["pos"] for x in answer_with_pos if not x["is_correct"]]

        test_grid = [
            (pos_not_correct, False, 1, "deactivate", True),
            (pos_correct, True, 1, "deactivate", False),
            (pos_not_correct, False, 1, "deactivate", False),
        ]

        self._test_scenario_select(fragment, test_grid)

    def test_scenario_3_select(self):
        fragment_slug = (
            "chapitre-tests$notion-fragments$serie-all-fragments$tous-les-fragments$17"
        )
        fragment = Fragment.objects.filter(slug=fragment_slug).first()
        fragment = model_to_dict(fragment)

        # Prepare the correct and not correct pos
        choices = fragment["data"]["answer"]["value"]["choices"]
        answer_with_pos = add_pos_to_choices(choices, keep_is_correct=True)
        pos_correct = [x["pos"] for x in answer_with_pos if x["is_correct"]]
        pos_not_correct = [x["pos"] for x in answer_with_pos if not x["is_correct"]]

        test_grid = [
            (pos_correct + pos_not_correct, False, 1, "deactivate", True),
            (pos_not_correct, False, 1, "deactivate", False),
            (pos_correct, True, 1, "deactivate", False),
        ]

        self._test_scenario_select(fragment, test_grid)
