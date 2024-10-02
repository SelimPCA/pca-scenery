import tempfile
from pprint import pprint

from app.teachers.math.generate_latex import generate_latex
from app.tests.teachers.utils import iter_on_solved_exprs_from_md
from app.tests.views.manifest_parser import ManifestParser
from app.tests.views.metatest import MetaTest
from app.tests.utils import snake_to_camel_case
from app.tests.teachers.utils import generate_wrong_sympy

import django.test

import sympy as sp


def tests_from_markdowns():

    # TODO: consider using generated latex

    view_name = "interaction_v1"
    folder = "seconde/tutoriels"

    for file, fragment_pos, answer, expr_sy in iter_on_solved_exprs_from_md(folder):

        if file != "9-05.md":
            continue

        origin = file.replace(".md", "")
        url_parameters_origin = f"{folder}/{origin}"

        latex_gt = answer.get("perfect_test", None)

        if latex_gt is None:
            continue

        latex_gt = latex_gt.replace("\\", "\\\\")

        variable = answer.get("variable", None)
        if variable:
            variable = sp.Symbol(variable)

        expr_wrong = generate_wrong_sympy(expr_sy)
        latex_wrong = generate_latex(expr_wrong, variable)
        latex_wrong = latex_wrong.replace("\\", "\\\\")

        # print("HERE", latex_gt, latex_wrong, expr_sy)

        set_up_test_data = b"""
        set_up_test_data:
        - reset_db
        - create_testuser: !common-item TESTUSER
        """

        set_up = b"""
        set_up:
        - login: !common-item CREDENTIALS
        """

        cases = f"""
        cases:
            {fragment_pos}_PERFECT_MATHS:
                answer:
                    !common-item 
                        ID: INTERACTION_BASE
                        interaction_ftype: maths_
                        fragment_pos: {fragment_pos}
                        fragment_id: {fragment_pos}
                        flag_id: flag-{fragment_pos}-dynamic
                        user_answer_latex: "{latex_gt}"
                        flag: 30
            {fragment_pos}_WRONG_MATHS:
                answer:
                    !common-item 
                        ID: INTERACTION_BASE
                        interaction_ftype: maths_
                        fragment_pos: {fragment_pos}
                        fragment_id: {fragment_pos}
                        flag_id: flag-{fragment_pos}-dynamic
                        user_answer_latex: "{latex_wrong}"
                        flag: 31
        """

        scene = f"""
        scene:
            method: POST
            url: app:{view_name}
            url_parameters: 
                origin: {url_parameters_origin}
                id_or_pos_min: !case answer:fragment_pos
            data: !case answer
            directives:
                - status_code: 201
                - count_instances:
                    model: UserInteraction
                    n: 1
                - dom_element:
                    find:
                        id : !case answer:flag_id
                    attribute: 
                        name: data-flag
                        value: !case answer:flag
        """

        # print(scene)

        # print("\n")
        # print('\n')

        # TODO
        # manifest.manifest_origin = (
        #     f"dynamically-from-{url_parameters_origin}-{fragment_pos}"
        # )

        with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
            fp.write(set_up_test_data)
            fp.write(set_up)
            fp.write(bytes(cases, encoding="utf8"))
            fp.write(bytes(scene, encoding="utf8"))
            fp.close()
            manifest = ManifestParser.parse_yaml(fp.name)

            # print(manifest)

        snake_origin = origin.replace("-", "_")
        testcase_name = (
            f"Test{snake_to_camel_case(view_name)}{snake_to_camel_case(snake_origin)}"
        )
        cls = MetaTest(testcase_name, (django.test.TestCase,), manifest)

        generated_latex = "generate_latex" in answer.keys()

        yield cls, generated_latex


if __name__ == "__main__":

    # NOTE: similar to metatest.py (discoverer and loader)
    # TODO: writr as loader and runner

    import logging

    from app.tests.utils import (
        colorize,
        tabulate,
    )

    from django.test.utils import get_runner
    from django.conf import settings

    from app.tests.views.unittest import serialize_result, pretty_test_name

    # SETTINGS
    ############

    verbosity = 1

    logger = logging.getLogger(__package__)
    runner = get_runner(
        settings, test_runner_class="django.test.runner.DiscoverRunner"
    )()
    loader = runner.test_loader
    suite_cls = runner.test_suite

    # LOADER
    ##############

    tests_suites = []

    for cls, generated_latex in tests_from_markdowns():
        tests = loader.loadTestsFromTestCase(cls)
        for test in tests:

            test_name = pretty_test_name(test)

            print(f"Discovered {test_name}")
            suite = suite_cls()
            suite.addTest(test)
            tests_suites.append((test_name, generated_latex, suite))

    # RUNNER
    #################

    for test_name, generated_latex, suite in tests_suites:
        result = runner.run_suite(suite)
        result_serialized = serialize_result(result)
        # results[test_name] = result_serialized

        # print("******************")
        # print(test_name, generated_latex)

        if result.errors or result.failures:
            log_lvl, color = logging.ERROR, "red"  # TODO: verbose should be an enum
        else:
            log_lvl, color = logging.INFO, "green"
        logger.log(
            log_lvl,
            f"{test_name} (generated_latex={generated_latex})\n{tabulate(result_serialized)}",
        )
        if verbosity > 0:
            print(
                f"{colorize(color, test_name)} (generated_latex={generated_latex})\n{tabulate({key: val for key, val in result_serialized.items() if val > 0})}"
            )

        # Log / verbosity
        for head, traceback in result.failures + result.errors:
            msg = f"{test_name}\n{head}\n{traceback}"
            logger.error(msg)
            if verbosity > 0:
                print(msg)
