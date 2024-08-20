"""Test the package `pca-scenery` itself."""

import unittest

# import rehearsal.tests

import rehearsal

discoverer = rehearsal.Discoverer()
runner = rehearsal.Runner()
tests_discovered = discoverer.discover(verbosity=2)
runner.run(tests_discovered, verbosity=2)

# TODO: remove and go through cli only ?
# TODO: should be run_suite_from_module(module)

# loader = unittest.loader.TestLoader()
# runner = unittest.TextTestRunner()
# suite = loader.loadTestsFromModule(rehearsal.tests)
# runner.run(suite)
# for test in suite:
#     print(test)
