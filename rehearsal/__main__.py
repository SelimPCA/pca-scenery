"""Test the package `pca-scenery` itself."""

import unittest

import rehearsal.tests

# TODO: remove and go through cli only ?
# TODO: should be run_suite_from_module(module)

loader = unittest.loader.TestLoader()
runner = unittest.TextTestRunner()
suite = loader.loadTestsFromModule(rehearsal.tests)
runner.run(suite)