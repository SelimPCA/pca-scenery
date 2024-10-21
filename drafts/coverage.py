"""Compute test coverage accroding to different criteria"""

import inspect
import importlib
import unittest
import sys
import io
from trace import Trace, CoverageResults
import ast
from functools import partial, cache, cached_property
import re
import linecache

import logging


from collections import defaultdict

from abc import ABC, abstractmethod


from logging import Logger

from app.tests.views import SysConfig
from app.tests.utils import snake_to_camel_case, tabulate, graph_bar, colorize
from app.tests.views.metatest import MetaTestDiscoverer

from django.urls import get_resolver


class CustomTrace(Trace):

    def __init__(
        self,
        count: int = 1,
        trace: int = 1,
        countfuncs: int = 0,
        countcallers: int = 0,
        ignoremods=(),
        ignoredirs=(),
        infile: str | None = None,
        outfile: str | None = None,
        timing: bool = False,
    ) -> None:
        """This is done to be able to have branch coverage"""

        super().__init__(
            count,
            trace,
            countfuncs,
            countcallers,
            ignoremods,
            ignoredirs,
            infile,
            outfile,
            timing,
        )

        # self._previous_line = (None, None)
        # TODO: add branches argument and make everything below optionnal
        # self._old_globaltrace = self.globaltrace
        # self.globaltrace = self.custom_globaltrace
        # self._old_localtrace = self.localtrace
        # self.localtrace = self.custom_localtrace
        # self.stack = []
        # self.call_counts = {}
        # self.branches = {}

    @property
    def current_call_id(self):
        return self.stack[-1]

    def custom_globaltrace(self, frame, why, arg):
        if why == "call":
            filename = frame.f_globals["__file__"]
            # filename = frame.f_code.co_filename
            funcname = frame.f_code.co_name
            call_origin = (filename, funcname)
            if filename.startswith(f"{SysConfig.src}"):  # TODO: is this right?
                self.call_counts[call_origin] = self.call_counts.get(call_origin, 0) + 1
                call_id = call_origin + (self.call_counts[call_origin],)
                self.stack.append(call_id)

        return self._old_globaltrace(frame, why, arg)

    def custom_localtrace(self, frame, why, arg):
        if why == "line":
            # record the file name and line number of every trace
            # filename = frame.f_code.co_filename
            # funcname = frame.f_code.co_name
            lineno = frame.f_lineno
            self.branches[self.current_call_id] = self.branches.get(
                self.current_call_id, []
            ) + [lineno]
        elif why == "return" or why == "exception":
            self.stack.pop()
        return self._old_localtrace(frame, why, arg)


##############################################
# ABSTRACT CLASS
##############################################


class CoverageRunner(ABC):

    # def __init__(self):
    # self.logger = logger

    ###################################
    # Abstract
    ###################################

    @property
    @abstractmethod
    def logger(self) -> Logger:
        """This should return the logger"""

    @property
    @abstractmethod
    def tested_modules(self):
        """This should return the list of all tested modules (module_name, module)."""

    @property
    @abstractmethod
    def testcases(self):
        """This should return the list of all written testcases (TestCase_name, TestCase)."""

    @abstractmethod
    def is_testcase_of(self, obj_name, obj, testcase_name):
        """Returns a boolean indicating whether `testcase_name` indicates that it is testing `obj`."""
        if inspect.isfunction(obj):
            obj_name = snake_to_camel_case(obj_name)
        elif inspect.isclass(obj):
            pass
        else:
            raise TypeError(f"Unexpected object {obj} of type {type(obj)}")

        re_match = re.match(r"^" + f"Test{obj_name}" + r"([A-Z]|$)", testcase_name)

        return bool(re_match)

    ###################################
    # Helpers
    ###################################

    # Static methods
    ################

    @staticmethod
    def is_defined_in(module, obj):
        """Indicates if `obj` is defined in `module`."""
        return inspect.getmodule(obj) == module

    @staticmethod
    def get_module_members(module):
        """Returns all objects found in `module` and which are defined in `module`."""
        is_defined_in_module = partial(CoverageRunner.is_defined_in, module)
        return inspect.getmembers(module, is_defined_in_module)

    @staticmethod
    def is_method_of(obj, attr):
        """Indicates if `attr` is a method of `obj`."""
        # We check hasattr because __abstractmethods__ from MetaTest would raise an error otherwise
        return hasattr(obj, attr) and callable(getattr(obj, attr))

    @staticmethod
    def get_methods(obj, dunder=False):
        """Returns all methods of `obj` excluding or not dunder methods through the parameter `dunder`."""
        is_method_of_obj = partial(CoverageRunner.is_method_of, obj)
        methods = filter(is_method_of_obj, dir(obj))
        if not dunder:
            methods = filter(lambda attr: not attr.startswith("__"), methods)
        return map(lambda attr: (attr, getattr(obj, attr)), methods)

    @cache
    def get_testcases_trace(
        self, obj_name, obj, *, count: bool, countfuncs: bool, trace: bool
    ) -> CoverageResults:

        if not countfuncs + count + trace == 1:
            # why is it the case ? The trace seems buggy otherwise
            raise ValueError(
                "Only one and only out of `countfuncs`, `count` and `trace` can be equal to True."
            )

        # tracer = Trace(
        tracer = CustomTrace(
            count=count,
            countfuncs=countfuncs,
            trace=trace,
            countcallers=0,
            # outfile=output,
            ignoredirs=[SysConfig.stdlib, SysConfig.purelib],
        )

        loader = unittest.TestLoader()
        runner = unittest.TextTestRunner(stream=io.StringIO())
        suite = unittest.TestSuite()
        for testcase_name, testcase in self.get_dedicated_testcases(obj_name, obj):

            tests = loader.loadTestsFromTestCase(testcase)
            suite.addTests(tests)

        # We silent the logger to avoid duplicate with rehearsal
        # TODO: should be a context manager
        logger_app = logging.getLogger("app.close_watch")
        logger_rehearsal = logging.getLogger(__package__ + ".rehearsal")
        logger_rehearsal_django = logging.getLogger(__package__ + ".rehearsal.django")
        handlers_app = logger_app.handlers.copy()
        handlers_rehearsal = logger_rehearsal.handlers.copy()
        handlers_rehearsal_django = logger_rehearsal_django.handlers.copy()
        logger_app.handlers = []
        logger_rehearsal.handlers = []
        logger_rehearsal_django.handlers = []

        tracer.runfunc(runner.run, suite)

        logger_app.handlers = handlers_app
        logger_rehearsal.handlers = handlers_rehearsal
        logger_rehearsal_django.handlers = handlers_rehearsal_django

        # if len(tracer.stack) != 0:
        # raise Exception("Stack was is not empty")

        return tracer.results()

    @staticmethod
    def find_executable_statements(module):
        """Returns the line numbers of executable statements in a Python module."""

        # TODO: cache
        # TODO: This should be done at the object level

        source = inspect.getsource(module)
        tree = ast.parse(source)

        source = source.splitlines()

        executable_lines = set()

        for node in ast.walk(tree):
            # Check if the node is an executable statement
            # TODO: /!\ liste vient de chatgpt
            if isinstance(
                node,
                (
                    ast.Expr,
                    ast.Assign,
                    ast.AugAssign,
                    ast.AnnAssign,
                    ast.For,
                    ast.While,
                    ast.If,
                    ast.With,
                    ast.Try,
                    ast.Assert,
                    ast.Import,
                    ast.ImportFrom,
                    ast.Call,
                    ast.Return,
                    ast.Raise,
                    ast.Yield,
                    ast.YieldFrom,
                    ast.Global,
                    ast.Nonlocal,
                    ast.Delete,
                    ast.Pass,
                    ast.Break,
                    ast.Continue,
                ),
            ):
                statement_source = tuple(source[node.lineno - 1 : node.end_lineno])
                executable_lines.add(
                    (
                        node.lineno,
                        node.end_lineno,
                        statement_source,
                    )
                )

        # TODO should I seek all exectuable lines or statements? this can be chekced if it coincides
        # if isinstance(node, ast.stmt):
        #     print(node.lineno)
        # else:
        #     pass
        # print("Not a statement", node)

        return sorted(executable_lines, key=lambda x: x[0])

    # Iterators
    ###########

    def get_tested_objects(self):
        # TODO: cached?
        for module_name, module in self.tested_modules:
            for obj_name, obj in self.get_module_members(module):
                yield (module_name, module, obj_name, obj)

    def get_dedicated_testcases(self, obj_name, obj):
        is_dedicated_testcase = partial(self.is_testcase_of, obj_name, obj)
        return filter(
            lambda x: is_dedicated_testcase(x[0]),
            self.testcases,
        )

    ###################################
    # 1.a) TestCase exists
    ###################################

    def testcase_exists(self, obj_name, obj):
        testcases = self.get_dedicated_testcases(obj_name, obj)
        return len(list(testcases)) > 0

    def coverage_testcases(self):
        """
        Test for all objects in all tested modules whether at least one TestCase is dedicated to it.

        The expected TestCase for a given object `object_name` should start with `TestObjectName`
        """
        report = {}
        for module_name, _, obj_name, obj in self.get_tested_objects():
            report[f"{module_name}.{obj_name}"] = self.testcase_exists(obj_name, obj)

        return report

    ###################################
    # 1.b) TestCase.test exists
    ###################################

    def test_exists(self, obj_name, obj, method_name):
        return any(
            hasattr(testcase, f"test_{method_name}")
            and self.is_method_of(testcase, f"test_{method_name}")
            for _, testcase in self.get_dedicated_testcases(obj_name, obj)
        )

    def coverage_tests(self):
        """
        Test for all methods of all objects in all tested modules whether a TestCase.test is dedicated to it.

        The expected TestCase for a given object `object_name` should be `TestObjectName`
        The expected test for a given method `method_name` should be `test_method_name`
        """
        report = {}
        for module_name, _, obj_name, obj in self.get_tested_objects():
            for method_name, _ in self.get_methods(obj):
                # TODO: are we sure we don't want to test some dunder methods?
                report[f"{module_name}.{obj_name}.{method_name}"] = self.test_exists(
                    obj_name, obj, method_name
                )
        return report

    ######################
    # 2. Function coverage
    ######################

    @abstractmethod
    def expected_function_trace(self, module_name, function_name):
        """Returns the trace expected to be found by the call of a given function"""

    def is_function_called(
        self, module_name, function_name, tracer_results: CoverageResults
    ):
        expected_trace = self.expected_function_trace(module_name, function_name)
        # print(tracer_results.calledfuncs)
        return expected_trace in tracer_results.calledfuncs

    def coverage_functions(self):
        """
        For a given module, test whether there all methods of each object, each functions are called.
        """
        report = {}

        for module_name, _, obj_name, obj in self.get_tested_objects():

            tracer_results = self.get_testcases_trace(
                obj_name, obj, count=False, countfuncs=True, trace=False
            )

            if inspect.isclass(obj):
                for method_name, _ in self.get_methods(obj):
                    # TODO: are we sure we don't want to test some dunder methods?
                    report[f"{module_name}.{obj_name}.{method_name}"] = (
                        self.is_function_called(
                            module_name, method_name, tracer_results
                        )
                    )
            elif inspect.isfunction(obj):
                report[f"{module_name}.{obj_name}"] = self.is_function_called(
                    module_name, obj_name, tracer_results
                )
            else:
                raise TypeError(
                    f"Unexpected type {type(obj)} when checking the function coverage for {obj}"
                )

            # break

        return report

    #######################
    # 3. Statement coverage
    #######################

    @abstractmethod
    def expected_statement_trace(self, module_name, lineno):
        """Returns the trace expected to be found by the call of a given statement"""

    def is_statement_executed(
        self, module_name, lineno, tracer_results: CoverageResults
    ):
        expected_trace = self.expected_statement_trace(module_name, lineno)
        return expected_trace in tracer_results.counts

    def coverage_executable_statements(self):

        result = {}
        for module_name, module, obj_name, obj in self.get_tested_objects():

            tracer_results = self.get_testcases_trace(
                obj_name, obj, count=True, countfuncs=False, trace=False
            )
            statements = self.find_executable_statements(module)

            result[module_name] = result.get(module_name, defaultdict(lambda: False))
            for lineno, endlineno, source in statements:
                if not result[module_name][(lineno, source)]:
                    result[module_name][(lineno, source)] = self.is_statement_executed(
                        module_name, lineno, tracer_results
                    )

        return result

    ##########################
    # 4. Branches coverage
    ##########################

    def coverage_branches(self):
        raise NotImplementedError
        # report = {}
        # for module_name, module, obj_name, obj in self.get_tested_objects():
        #     tracer_results = self.get_testcases_trace(
        #         obj_name, obj, count=False, countfuncs=False, trace=True
        #     )
        #     break
        # return report

    ##########################
    # 5. TODO
    ##########################

    """
    https://en.wikipedia.org/wiki/Code_coverage
    
    - loop coverage, edge coverage, condition coverage, mutltiple condition
    - Modified condition/decision coverage (https://en.wikipedia.org/wiki/Modified_condition/decision_coverage)
    
    Test coverage is one consideration in the safety certification of avionics equipment. The guidelines by which avionics gear is certified by the Federal Aviation Administration (FAA) is documented in DO-178B[16] and DO-178C.[18]
    Test coverage is also a requirement in part 6 of the automotive safety standard ISO 26262 Road Vehicles - Functional Safety
    


    """

    ##########################
    # RUN
    ##########################

    def run(
        self,
        *,
        testcase: bool,
        test: bool,
        function: bool,
        statement: bool,
        branch: bool,
    ):

        self.logger.debug(f"Launching coverage...")

        result = {}

        # Check TestCases are defined
        if testcase:
            self.logger.debug("Launching testcase coverage...")
            result["testcase"] = self.coverage_testcases()
            self.logger.info(f"Testcase coverage: \n{tabulate(result['testcase'])}")

        # Check TestCases.test_method are defined
        if test:
            self.logger.debug("Launching test coverage...")
            result["test"] = self.coverage_tests()
            self.logger.info(f"Test coverage: \n{tabulate(result['test'])}")

        # Check all functions of classes are executed
        if function:
            self.logger.debug("Launching function coverage...")
            result["function"] = self.coverage_functions()
            self.logger.info(f"Function coverage: \n{tabulate(result['function'])}")

        # Check all statements are executed
        if statement:
            self.logger.debug("Launching statement coverage...")
            result["statement"] = self.coverage_executable_statements()
            for module_name, result_module in result["statement"].items():
                for (lineno, source), is_executed in result_module.items():
                    if not is_executed:
                        source_fmt = "".join(l.strip() for l in source)
                        self.logger.debug(
                            f"{module_name}-{lineno} is not executed\n{source_fmt}"
                        )
            stats = {
                module_name: sum(dict(result_module).values()) / len(result_module)
                for module_name, result_module in result["statement"].items()
            }
            result["statement"]["STATS"] = stats
            self.logger.info(
                f"Statement coverage: \n{tabulate(result['statement']["STATS"])}"
            )

        # Check if possible branches are being executed
        if branch:
            self.logger.debug("Launching branch coverage...")
            # result["branch"] = self.coverage_branches()
            # self.logger.info(f"Branch coverage: \n{tabulate(result['branch'])}")

        return result


##############################################
# CONCRETE CLASSES
##############################################


class RehearsalCoverageRunner(CoverageRunner):

    @property
    def logger(self):
        return logging.getLogger(__package__ + ".rehearsal")

    @cached_property
    def tested_modules(self):
        package = importlib.import_module(__package__)
        tested_modules = []
        for module_name, module in inspect.getmembers(package, inspect.ismodule):
            if origin := module.__spec__.origin:
                if origin.startswith(f"{SysConfig.src}/{SysConfig.this_folder}"):
                    if module_name not in ["rehearsal", "coverage", "unittest"]:
                        # TODO: technically we could test coverage and unittest
                        tested_modules.append((module_name, module))
        return tested_modules

    @cached_property
    def testcases(self):

        testcases = inspect.getmembers(
            importlib.import_module(".rehearsal", package=__package__),
            inspect.isclass,
        )
        testcases = [
            (cls_name, cls)
            for cls_name, cls in testcases
            if issubclass(cls, unittest.TestCase)
        ]

        return testcases

    def is_testcase_of(self, obj_name, obj, testcase_name):
        return super().is_testcase_of(obj_name, obj, testcase_name)

    def expected_function_trace(self, module_name, function_name):
        return (
            f"{SysConfig.src}/{SysConfig.this_folder}/{module_name}.py",
            module_name,
            function_name,
        )

    def expected_statement_trace(self, module_name, lineno):
        return (
            f"{SysConfig.src}/{SysConfig.this_folder}/{module_name}.py",
            lineno,
        )


class MetatestCoverageRunner(CoverageRunner):

    @property
    def logger(self):
        return logging.getLogger(__package__)

    @cached_property
    def tested_modules(self):
        resolver = get_resolver("app.urls")
        # TODO: this is for testing
        view_names = ["login", "register", "interaction_v1", "highschool"]
        url_patterns = filter(lambda x: x.name in view_names, resolver.url_patterns)
        tested_modules = [
            inspect.getmodule(url_pattern.callback) for url_pattern in url_patterns
        ]
        tested_modules = [(module.__name__, module) for module in tested_modules]

        return tested_modules

    @cached_property
    def testcases(self):
        testcases = list(MetaTestDiscoverer().discover())
        testcases = [(testcase.__name__, testcase) for _, testcase in testcases]
        return testcases

    def is_testcase_of(self, obj_name, obj, testcase_name):
        if inspect.isfunction(obj) and obj_name.endswith("_view"):
            obj_name = obj_name.replace("_view", "")
            return super().is_testcase_of(obj_name, obj, testcase_name)
        elif inspect.isfunction(obj):
            self.logger.warning(f"Unexpectedly named object: {obj_name}")
            return False
        else:
            raise TypeError(
                f"Expected function not {type(obj)} when checking the existence of testcase for {obj}"
            )

    def test_exists(self, obj_name, obj, method_name):
        """The metatesting process generate a single `test` function for any TestCase"""
        raise NotImplementedError

    def expected_function_trace(self, module_name, function_name):
        expected_trace = (
            f"{SysConfig.src}/{module_name.replace('.', '/')}.py",
            module_name.split(".")[-1],
            function_name,
        )
        return expected_trace

    def expected_statement_trace(self, module_name, lineno):
        return (
            f"{SysConfig.src}/{module_name.replace('.', '/')}.py",
            lineno,
        )

    def run(
        self,
        *,
        testcase: bool,
        function: bool,
        statement: bool,
        branch: bool,
    ):
        return super().run(
            testcase=testcase,
            test=False,
            function=function,
            statement=statement,
            branch=branch,
        )


######################################################################


# def get_origin(self, obj):
#     """Return the origin of an object"""
#     module = inspect.getmodule(obj)
#     if module is None:  # Dunder objects like __file__ etc...
#         # print(obj, dir(obj))
#         return None
#     origin = module.__spec__.origin
#     if origin == "built-in":  # Built-in objects like sys
#         return "built-in"
#     if origin == "frozen":  # Built-in objects like sys
#         return "frozen"
#     elif origin.startswith(self.sys_config.stdlib):  # Standard python library
#         return "stdlib"
#     elif origin.startswith(
#         self.sys_config.purelib
#     ):  # Site packages (non platform dependent)
#         return "purelib"
#     elif (
#         origin
#         == f"{self.sys_config.src}/{self.sys_config.this_folder}/rehearsal.py"
#     ):
#         return "rehearsal"
#     elif (
#         origin == f"{self.sys_config.src}/{self.sys_config.this_folder}/coverage.py"
#     ):
#         return "coverage"
#     elif origin.startswith(f"{self.sys_config.src}/{self.sys_config.this_folder}"):
#         return "scenery"
#     elif origin.startswith(self.sys_config.src):
#         return "app"
#     else:
#         raise Exception(f"Cannot solve origin {origin}")


######################
# INSPECT DEPENDENCIES
######################

#      Run the testing routine for all object
#
#         origin = self.resolve_origin(obj)
#         if origin in [None, "built-in", "frozen", "stdlib"]:
#             continue
#         elif origin == "purelib":
#             pass
#         elif origin == "this-app":
#             pass
#         elif origin == "this-folder":
#             # Filter on object from the currently inspected module
#             if module.__name__ != obj.__module__:
#                 continue
#             self._inspecting_routine(testcase, obj)
#         else:
#             raise Exception
