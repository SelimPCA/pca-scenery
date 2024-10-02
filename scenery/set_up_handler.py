import importlib
import logging
import os

import scenery.manifest

import django.test


class SetUpHandler:
    """
    Responsible for executing instructions used in `TestCase.setUp` and `TestCase.setUpTestData`
    provided in the manifest.
    In practice, the MethodBuilder will build functions that use the SetUpHandler to execute
    `SetUpInstruction`
    """

    module = importlib.import_module(
        os.getenv("SCENERY_SET_UP_INSTRUCTIONS"),
    )

    @staticmethod
    def exec_set_up_instruction(
        django_testcase: django.test.TestCase,
        instruction: scenery.manifest.SetUpInstruction,
    ):
        """Execute the method corresponding to the SetUpInstruction"""

        func = getattr(SetUpHandler.module, instruction.command)
        func(django_testcase, **instruction.args)

        logger = logging.getLogger(__package__)
        logger.debug(f"Applied {instruction}")
