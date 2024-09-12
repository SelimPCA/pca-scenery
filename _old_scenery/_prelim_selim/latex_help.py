import datetime
import json
import logging

logging.disable(logging.ERROR)

from django.test import TestCase
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict

# Todo : use in user_answer
from django.shortcuts import get_object_or_404

# Data Loaders
from app.management.commands.load_content_custom import Command as LoadContentCommand

# For mock user creation
from app.models.accounts.user_custom import UserCustom

from app.serializers.listener.user_answer_maths import serialize_user_answer_maths


from app.teachers.emojy import replace_numbers_and_symbols_with_emojis_augmented


from app.serializers.content.block import add_pos_to_choices

from app.teachers.select.select_teacher import SelectTeacher

# Models
from app.models import Fragment

from pprint import pprint

from sympy import print_latex, simplify

from app.teachers.math.math_halfteacher import MathTeacher


from app.close_watch.close_watch import close_watch


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
        load_content_c.handle()
        # TODO  shouldnt be superuser and should use the Profile created
        cls.USER = UserCustom.objects.create_superuser(EMAIL, EMAIL, PASSWORD)

        cls.input_latex_types = [
            "perfect",
            "correct_not_ordered",
            "correct_not_computed",
            "not_correct",
        ]

    def setUp(self):
        self.client.login(username=EMAIL, password=PASSWORD)

    # TODO : add test empty
    def test_all_interactions_maths(self):
        """Test a POST for user_answer for all (interaction, input_latex_type in test)."""
        for fragment in Fragment.objects.filter(f_type="interaction-maths"):
            self._test_interaction_maths(fragment)
            # print("\n\n\n")

    def _test_interaction_maths(self, fragment):
        block = fragment.block
        fragment = model_to_dict(fragment)

        fragment_data_answer = fragment["data"]["answer"]

        latex_perfect = (
            fragment_data_answer.get("value", {})
            .get(
                "tests", {}
            )  # TODO very  CAREFUL : if any of this key is there but None it breaks
            .get("parser-latex", {})
            .get("input-latex", {})
            .get("perfect", "")
        )

        if latex_perfect:
            math_teacher = MathTeacher(block.__dict__.copy(), close_watch)
            story = math_teacher.direct(
                fragment_data_answer,
                latex_perfect,
                skip_if_latex_enough=False,
            )
            # print(story)
            print(fragment["data"]["instruction"])
            output_sy = story["answer"]["math_solver_output_sy"]
            output_sy_simplified = simplify(output_sy)
            print_latex(output_sy)
            print_latex(output_sy_simplified)
            print("\n")

        # self.assertIsCorrect(input_latex_type, is_correct)
        # self.assertIsCorrectLatex(input_latex_type, is_correct_latex)
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
