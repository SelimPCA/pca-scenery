import os


def main():
    """Test the package `scenery` itself."""

    result = {}

    # TODO: add parser and logger (see scenery.__main__)

    ###################
    # CONFIG SCENERY
    ###################

    os.environ["SCENERY_TESTED_APP"] = "some_app"
    os.environ["SCENERY_COMMON_ITEMS"] = "scenery/rehearsal/common_items.yml"
    os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = "scenery.rehearsal.set_up_instructions"

    # TODO: config env

    ###################
    # CONFIG DJANGO
    ###################

    import scenery.common

    scenery.common.django_setup(
        ROOT_URLCONF="scenery.rehearsal.project_django.project_django.urls",
        APP="scenery.rehearsal.project_django.some_app",
        DB_NAME="scenery/rehearsal/project_django/db.sqlite3",
    )

    #############
    # RUN TESTS
    #############

    import scenery.rehearsal

    discoverer = scenery.rehearsal.RehearsalDiscoverer()
    runner = scenery.rehearsal.RehearsalRunner()
    tests_discovered = discoverer.discover(verbosity=2)
    result["metatesting"] = runner.run(tests_discovered, verbosity=2)

    # TODO: output result


if __name__ == "__main__":
    import sys

    main()
    sys.exit(0)
    # TODO: depends on output actually ?
