"""Test the package `pca-scenery` itself."""

import os
import rehearsal


###################
# CONFIG ENV
###################


def main():
    os.environ["SCENERY_TESTED_APP"] = "some_app"
    os.environ["SCENERY_COMMON_ITEMS"] = "rehearsal/common_items.yml"
    os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = "rehearsal.set_up_instructions"

    discoverer = rehearsal.RehearsalDiscoverer()
    runner = rehearsal.RehearsalRunner()
    tests_discovered = discoverer.discover(verbosity=2)
    runner.run(tests_discovered, verbosity=2)


if __name__ == "__main__":
    main()
