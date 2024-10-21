import os


def main():
    """Test the package `scenery` itself."""

    result = {}

    #################
    # PARSE ARGUMENTS
    #################

    # TODO

    ####################
    # LOGGERS
    ####################

    # TODO

    ###################
    # CONFIG SCENERY
    ###################

    rehearsal_dir = os.path.abspath(os.path.join(__file__, os.pardir))

    print("REHEARSAL DIR", rehearsal_dir)

    # Scenery
    # NOTE: should be consistent with scenery.common.scenery_setup()
    os.environ["SCENERY_COMMON_ITEMS"] = f"{rehearsal_dir}/common_items.yml"
    os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = "rehearsal.set_up_instructions"
    os.environ["SCENERY_TESTED_APP_NAME"] = "some_app"
    os.environ["SCENERY_MANIFESTS_FOLDER"] = f"{rehearsal_dir}/manifests"

    ###################
    # CONFIG DJANGO
    ###################

    import scenery.common

    scenery.common.django_setup("rehearsal.project_django.project_django.settings")

    #############
    # RUN TESTS
    #############

    import rehearsal

    discoverer = rehearsal.RehearsalDiscoverer()
    runner = rehearsal.RehearsalRunner()
    tests_discovered = discoverer.discover(verbosity=2)
    result["testing"] = runner.run(tests_discovered, verbosity=2)

    from scenery.metatest import MetaTestRunner, MetaTestDiscoverer

    discoverer = MetaTestDiscoverer()
    tests_discovered = discoverer.discover(verbosity=2)
    runner = MetaTestRunner()
    result["metatesting"] = runner.run(tests_discovered, verbosity=2)

    ###############
    # OUTPUT RESULT
    ###############

    # TODO


if __name__ == "__main__":
    import sys

    main()
    sys.exit(0)
