from django.test import TestCase, Client


from app.tests.views.dataclasses import HttpTake
from app.tests.views.enums import SetUpCommand
from app.tests.views.set_up_handler import SetUpHandler
from app.tests.views.checker import HttpChecker
from app.tests.views.io import IO

################
# METHOD BUILDER
################


class MethodBuilder:

    @staticmethod
    def build_setUpTestData(instructions: list[SetUpCommand]):

        def setUpTestData(self: TestCase):

            for instruction in instructions:
                SetUpHandler.exec_set_up_instruction(self, instruction)

        return classmethod(setUpTestData)

    @staticmethod
    def build_setUp(instructions: list[SetUpCommand]):

        def setUp(self: TestCase):
            self.client = (
                Client()
            )  # TODO: normal que ce soit juste la ? I don't think so
            for instruction in instructions:
                SetUpHandler.exec_set_up_instruction(self.client, instruction)

        return setUp

    @staticmethod
    def build_test_from_take(take: HttpTake):

        def test(self: TestCase):
            response = IO.get_http_client_response(self.client, take)
            for i, check in enumerate(take.checks):
                with self.subTest(i=i):
                    HttpChecker.exec_check(self, response, check)

        return test
