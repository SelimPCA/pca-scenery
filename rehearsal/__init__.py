import io
import os
import logging
from types import TracebackType
import unittest

import django
from django.conf import settings as django_settings
from django.apps import apps as django_apps
from django.test.runner import DiscoverRunner
from django.test.utils import get_runner

###################
# CONFIG ENV
###################

os.environ["SCENERY_TESTED_APP"] = "some_app"
os.environ["SCENERY_COMMON_ITEMS"] = "rehearsal/common_items.yml"

###################
# CONFIG DJANGO
###################

django_settings.configure(
    ROOT_URLCONF="rehearsal.project_django.project_django.urls",
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        # Add other apps here
        "rehearsal.project_django.some_app",
    ],
    DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "rehearsal/project_django/db.sqlite3",
    }
}
)
django.setup()



####################################
# UNITTEST AUGMENTATION
####################################


def serialize_result(result: unittest.TestResult) -> dict:
    result: dict = {
        attr: getattr(result, attr)
        for attr in [
            "failures",
            "errors",
            "testsRun",
            "skipped",
            "expectedFailures",
            "unexpectedSuccesses",
        ]
    }
    result = {
        key: len(val) if isinstance(val, list) else val for key, val in result.items()
    }
    return result


def pretty_test_name(test: unittest.TestCase):
    return f"{test.__module__}.{test.__class__.__qualname__}.{test._testMethodName}"


class CustomTestResult(unittest.TestResult):
    """
    Modify the addError method just to store the type of exception caught
    to be able to have a nice self.assertTestRaises wich has
    the expected_exception as argument
    """

    def addError(
        self,
        test: unittest.TestCase,
        err: (
            tuple[type[BaseException], BaseException, TracebackType]
            | tuple[None, None, None]
        ),
    ) -> None:

        super().addError(test, err)
        self.caught_exception = err


class CustomTestCase(unittest.TestCase):
    """This class augment unittest.TestCase for logging puposes"""

    @classmethod
    def log_db(cls):
        # TODO: this depends on django
        app_config = django_apps.get_app_config(os.getenv("SCENERY_TESTED_APP"))
        for model in app_config.get_models():
            cls.logger.debug(f"{model.__name__}: {model.objects.count()} instances.")

    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger(__package__ + ".rehearsal")
        cls.logger.debug(f"{cls.__module__}.{cls.__qualname__}.setUpClass")
        cls.log_db()

    @classmethod
    def tearDownClass(cls):
        cls.logger.debug(f"{cls.__module__}.{cls.__qualname__}.tearDownClass")
        cls.log_db()

    def setUp(self):
        self.logger.debug(f"{self.__module__}.{self.__class__.__qualname__}.setUp")
        self.log_db()

    def tearDown(self):
        self.logger.debug(f"{self.__module__}.{self.__class__.__qualname__}.tearDown")
        self.log_db()


####################################
# DJANGO TESTCASE AUGMENTATION
####################################


def overwrite_get_runner_kwargs(django_runner: DiscoverRunner, stream):
    """
    see django.test.runner.DiscoverRunner.get_runner_kwargs
    this is done to avoid to print the django tests output
    """
    kwargs = {
        "failfast": django_runner.failfast,
        "resultclass": django_runner.get_resultclass(),
        "verbosity": django_runner.verbosity,
        "buffer": django_runner.buffer,
    }
    kwargs.update({"stream": stream})
    return kwargs


class TestCaseOfDjangoTestCase(CustomTestCase):
    """
    This class augments the unittest.TestCase such that it is able to:
    - take a django.test.TestCase and run it via the django test runner
    - make assertions on the result of the django TestCase (sucess ,failures and errors)
    - customize the output of the django.test.TestCase
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.django_loader = unittest.TestLoader()
        TestRunner = get_runner(django_settings)
        cls.django_runner: DiscoverRunner = TestRunner()
        # Customized for better exception catching
        cls.django_runner.test_runner.resultclass = CustomTestResult

        # We customize the django testrunner to avoid confusion in the output and django vs unittest
        cls.django_stream = io.StringIO()

        # Bind the new method
        def overwrite(runner):
            return overwrite_get_runner_kwargs(runner, cls.django_stream)

        cls.django_runner.get_test_runner_kwargs = overwrite.__get__(cls.django_runner)

        cls.logger_django = logging.getLogger(__package__ + ".rehearsal.django")
        # TODO use unittest.TestCase(logger)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.django_stream.close()

    def setUp(self):
        super().setUp()
        # We create a django TestCase (customized) to which we will dynamically add setUpTestData, setUp and test_* functions
        self.django_testcase = type("DjangoTestCase", (django.test.TestCase,), {})

    def tearDown(self):
        super().tearDown()
        msg = self.django_stream.getvalue()
        self.logger_django.debug(f"{pretty_test_name(self)}\n{msg}")
        self.django_stream.seek(0)
        self.django_stream.truncate()

    def run_django_testcase(self):

        # TODO: log_db should be injected here with a much more detailed function

        suite = unittest.TestSuite()
        tests = self.django_loader.loadTestsFromTestCase(self.django_testcase)

        suite.addTests(tests)
        result = self.django_runner.run_suite(suite)
        self.logger_django.info(f"{repr(self)} {result}")
        return result

    def run_django_test(self, django_test) -> CustomTestResult:
        suite = unittest.TestSuite()
        suite.addTest(django_test)
        result = self.django_runner.run_suite(suite)
        return result

    def assertTestPasses(self, django_test):
        result = self.run_django_test(django_test)
        self.assertTrue(result.wasSuccessful(), f"{django_test} was not succesfull")

    def assertTestFails(self, django_test):
        result = self.run_django_test(django_test)
        self.assertFalse(result.wasSuccessful(), f"{django_test} was not succesfull")
        self.assertEqual(
            len(result.errors), 0, f"{django_test} did not raise any error"
        )

    def assertTestRaises(self, django_test, expected: BaseException):
        result = self.run_django_test(django_test)
        self.assertGreater(
            len(result.errors), 0, f"{django_test} did not raise any error"
        )
        self.assertIsNotNone(
            result.caught_exception, f"{django_test} did not caught any exception"
        )
        with self.assertRaises(
            expected, msg=f"{django_test} did not raise expected exception {expected}"
        ):
            raise result.caught_exception[0](result.caught_exception[1])
