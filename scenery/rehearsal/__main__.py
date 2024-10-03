import os


def main():
    """Test the package `scenery` itself."""

    result = {}

    #################
    # PARSE ARGUMENTS
    #################

    # TODO:

    ####################
    # LOGGERS
    ####################

    # TODO:
    # Rehearsal
    # logger_rehearsal = logging.getLogger(__package__ + ".rehearsal")
    # logger_rehearsal.addHandler(handler_full)
    # logger_rehearsal.setLevel(level)
    # logger_rehearsal.propagate = False

    # # Rehearsal django
    # logger_rehearsal_django = logging.getLogger(__package__ + ".rehearsal.django")
    # logger_rehearsal_django.addHandler(handler_full)
    # logger_rehearsal_django.setLevel(level)
    # # This is a bit brutal/rough/ugly
    # logger_rehearsal_django.manager.disable = logging.NOTSET
    # logger_rehearsal_django.propagate = False

    ###################
    # CONFIG SCENERY
    ###################

    rehearsal_dir = os.path.abspath(os.path.join(__file__, os.pardir))

    # Scenery
    os.environ["SCENERY_COMMON_ITEMS"] = f"{rehearsal_dir}/common_items.yml"
    os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = "scenery.rehearsal.set_up_instructions"
    os.environ["SCENERY_TESTED_APP_NAME"] = "some_app"

    ###################
    # CONFIG DJANGO
    ###################

    import scenery.common

    scenery.common.django_setup()

    #############
    # RUN TESTS
    #############

    import scenery.rehearsal

    discoverer = scenery.rehearsal.RehearsalDiscoverer()
    runner = scenery.rehearsal.RehearsalRunner()
    tests_discovered = discoverer.discover(verbosity=2)
    result["metatesting"] = runner.run(tests_discovered, verbosity=2)

    ###############
    # OUTPUT RESULT
    ###############

    # TODO


if __name__ == "__main__":
    import sys

    main()
    sys.exit(0)
