import os


def main():
    """Test the package `scenery` itself."""

    result = {}

    # TODO: add parser and logger (see scenery.__main__)

    ###################
    # CONFIG SCENERY
    ###################

    rehearsal_dir = os.path.abspath(os.path.join(__file__, os.pardir))

    # Scenery
    os.environ["SCENERY_COMMON_ITEMS"] = f"{rehearsal_dir}/common_items.yml"
    os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = "scenery.rehearsal.set_up_instructions"
    # Django
    os.environ["SCENERY_TESTED_APP_NAME"] = "some_app"
    os.environ["SCENERY_DB_NAME"] = f"{rehearsal_dir}/project_django/db.sqlite3"
    os.environ["SCENERY_ROOT_URLCONF"] = (
        "scenery.rehearsal.project_django.project_django.urls"
    )
    os.environ["SCENERY_INSTALLED_APPS"] = "scenery.rehearsal.project_django.some_app"
    # os.environ["SCENERY_MANIFESTS_FOLDER"] = None

    ###################
    # CONFIG DJANGO
    ###################

    import scenery.common

    scenery.common.django_setup(
        ROOT_URLCONF=os.getenv("SCENERY_ROOT_URLCONF"),
        APPS=os.getenv("SCENERY_INSTALLED_APPS").split(";"),
        DB_NAME=os.getenv("SCENERY_DB_NAME"),
    )

    #############
    # RUN TESTS
    #############

    import scenery.rehearsal

    discoverer = scenery.rehearsal.RehearsalDiscoverer()
    runner = scenery.rehearsal.RehearsalRunner()
    tests_discovered = discoverer.discover(verbosity=2)
    result["metatesting"] = runner.run(tests_discovered, verbosity=2)

    return result


if __name__ == "__main__":
    import sys

    main()
    sys.exit(0)
    # TODO: depends on output actually ?
