import os
import io
import logging
import itertools


from scenery.manifest import Manifest
from scenery.method_builder import MethodBuilder
from scenery.manifest_parser import ManifestParser
import scenery.common

import django.test
from django.test.utils import get_runner

from django.conf import settings


##############################
# META TESTING
##############################


class MetaTest(type):

    def __new__(cls, clsname, bases, manifest: Manifest):

        # Build setUpTestData and SetUp
        setUpTestData = MethodBuilder.build_setUpTestData(manifest.set_up_test_data)
        setUp = MethodBuilder.build_setUp(manifest.set_up)

        # Add SetupData and SetUp as methods of the Test class
        cls_attrs = {
            "setUpTestData": setUpTestData,
            "setUp": setUp,
        }

        for (case_id, case), (scene_pos, scene) in itertools.product(
            manifest.cases.items(), enumerate(manifest.scenes)
        ):
            # take = TakeBuilder.shoot(scene, case)
            take = scene.shoot(case)
            test = MethodBuilder.build_test_from_take(take)
            cls_attrs.update({f"test_case_{case_id}_scene_{scene_pos}": test})

        return super().__new__(cls, clsname, bases, cls_attrs)


class MetaTestDiscoverer:

    def __init__(self):
        self.logger = logging.getLogger(__package__)
        # This is done to allow the cohabitation of scenery
        # And python manage.py test ..., the latest using settings.TEST_RUNNER
        self.runner = get_runner(
            settings, test_runner_class="django.test.runner.DiscoverRunner"
        )()
        self.loader = self.runner.test_loader

    def discover(self, verbosity):
        """Returns a list of pair (test_name, suite), each suite contains a single test"""

        out = []

        suite_cls = self.runner.test_suite

        folder = os.getenv("SCENERY_MANIFESTS_FOLDER")

        for filename in os.listdir(folder):
            self.logger.debug(f"Discovered manifest '{folder}/{filename}'")

            manifest = ManifestParser.parse_yaml(os.path.join(folder, filename))

            # Create class
            filename = filename.replace(".yml", "")
            testcase_name = f"Test{scenery.common.snake_to_camel_case(folder)}{scenery.common.snake_to_camel_case(filename)}"
            cls = MetaTest(testcase_name, (django.test.TestCase,), manifest)

            # Log / verbosity
            msg = f"Discovered {cls.__module__}.{cls.__qualname__}"
            self.logger.debug(msg)
            if verbosity >= 2:
                print(msg)

            # Load
            tests = self.loader.loadTestsFromTestCase(cls)
            for test in tests:

                test_name = scenery.common.pretty_test_name(test)
                suite = suite_cls()
                suite.addTest(test)
                out.append((test_name, suite))

        return out


# from django.test.runner import DiscoverRunner


class MetaTestRunner:

    # TODO: this is VERY similar to rehearsalrunner.run
    # TODO: should probably take the discovered suite as argument
    # TODO: it should be a single TestsRunner

    def __init__(self):
        # TODO: get the discoverer out
        self.runner = get_runner(
            settings, test_runner_class="django.test.runner.DiscoverRunner"
        )()
        self.logger = logging.getLogger(__package__)
        self.discoverer = MetaTestDiscoverer()
        self.stream = io.StringIO()

        def overwrite(runner):
            return scenery.common.overwrite_get_runner_kwargs(runner, self.stream)

        self.runner.get_test_runner_kwargs = overwrite.__get__(self.runner)
        app_logger = logging.getLogger("app.close_watch")
        app_logger.propagate = False

    def __del__(self):
        # TODO: this is not totally reliable, a context manager would be ideal
        self.stream.close()
        app_logger = logging.getLogger("app.close_watch")
        app_logger.propagate = True

    def run(self, tests_discovered, verbosity):

        results = {}
        for test_name, suite in tests_discovered:

            result = self.runner.run_suite(suite)

            result_serialized = scenery.common.serialize_unittest_result(result)
            results[test_name] = result_serialized

            if result.errors or result.failures:
                log_lvl, color = logging.ERROR, "red"
            else:
                log_lvl, color = logging.INFO, "green"
            self.logger.log(
                log_lvl, f"{test_name}\n{scenery.common.tabulate(result_serialized)}"
            )
            if verbosity > 0:
                print(
                    f"{scenery.common.colorize(color, test_name)}\n{scenery.common.tabulate({key: val for key, val in result_serialized.items() if val > 0})}"
                )

            # Log / verbosity
            for head, traceback in result.failures + result.errors:
                msg = f"{test_name}\n{head}\n{traceback}"
                self.logger.error(msg)
                if verbosity > 0:
                    print(msg)

        return results
