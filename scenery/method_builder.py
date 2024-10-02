import django.test

import scenery.manifest
from scenery.http_checker import HttpChecker
from scenery.set_up_handler import SetUpHandler

################
# METHOD BUILDER
################


class MethodBuilder:

    @staticmethod
    def build_setUpTestData(instructions: list[str]):

        def setUpTestData(django_testcase: django.test.TestCase):

            for instruction in instructions:
                SetUpHandler.exec_set_up_instruction(django_testcase, instruction)

        return classmethod(setUpTestData)

    @staticmethod
    def build_setUp(instructions: list[str]):

        def setUp(django_testcase: django.test.TestCase):
            for instruction in instructions:
                SetUpHandler.exec_set_up_instruction(django_testcase, instruction)

        return setUp

    @staticmethod
    def build_test_from_take(take: scenery.manifest.HttpTake):

        def test(django_testcase: django.test.TestCase):
            response = HttpChecker.get_http_client_response(
                django_testcase.client, take
            )
            for i, check in enumerate(take.checks):
                with django_testcase.subTest(i=i):
                    HttpChecker.exec_check(django_testcase, response, check)

        return test
