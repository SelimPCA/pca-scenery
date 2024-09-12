import scenery.manifest
from scenery.http_checker import HttpChecker
from scenery.set_up_handler import SetUpHandler

import django.test

################
# METHOD BUILDER
################


class MethodBuilder:

    @staticmethod
    def build_setUpTestData(instructions: list[str]):

        def setUpTestData(self: django.test.TestCase):

            for instruction in instructions:
                SetUpHandler.exec_set_up_instruction(self, instruction)

        return classmethod(setUpTestData)

    @staticmethod
    def build_setUp(instructions: list[str]):

        def setUp(self: django.test.TestCase):
            self.client = (
                django.test.Client()
            )  # TODO: normal que ce soit juste la ? I don't think so
            for instruction in instructions:
                SetUpHandler.exec_set_up_instruction(self.client, instruction)

        return setUp

    @staticmethod
    def build_test_from_take(take: scenery.manifest.HttpTake):

        def test(self: django.test.TestCase):
            response = HttpChecker.get_http_client_response(self.client, take)
            for i, check in enumerate(take.checks):
                with self.subTest(i=i):
                    HttpChecker.exec_check(self, response, check)

        return test
