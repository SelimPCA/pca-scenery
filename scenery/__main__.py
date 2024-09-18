import argparse
import os
import logging


def main():

    result = {}

    #################
    # PARSE ARGUMENTS
    #################

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        type=int,
        default=2,
        help="Verbose output",
    )

    parser.add_argument(
        "--view",
        dest="restrict_view_name",
        action="store",
        default=None,
        help="Restrict to a specific view",
    )

    parser.add_argument(
        "--output",
        default=None,
        dest="output",
        action="store",
        help="Export output",
    )

    args = parser.parse_args()

    result["args"] = args.__dict__

    ####################
    # LOGGERS
    ####################

    # TODO: ajuster avec les micro secondes
    # TODO: move ?

    level = logging.DEBUG

    # Format
    format_log = "[%(asctime)s.%(msecs)03d] [%(name)s] [%(levelname)s] %(message)s"
    datefmt_ = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=format_log, datefmt=datefmt_)

    # Handlers
    if args.output:
        handler_full = logging.FileHandler(args.output, mode="w")
        handler_full.setFormatter(formatter)
        handler_full.setLevel(level)
    else:
        handler_full = logging.NullHandler()

    # Scenery
    logger = logging.getLogger(__package__)
    logger.addHandler(handler_full)
    logger.setLevel(level)

    # TODO: move this somewhere useful
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

    logger_app = logging.getLogger("logger_app")  # TODO: change? should be in env ?
    logger_app.handlers = []
    logger_app.addHandler(handler_full)
    logger_app.setLevel(level)

    ##################
    # CONFIG SCENERY
    ##################

    import dotenv

    has_config = dotenv.load_dotenv(".env_scenery")
    if not has_config:
        # TODO: this should actually become a test
        scenery_dir = os.path.abspath(os.path.join(__file__, os.pardir))

        # Scenery
        os.environ["SCENERY_COMMON_ITEMS"] = f"{scenery_dir}/rehearsal/common_items.yml"
        os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = (
            "scenery.rehearsal.set_up_instructions"
        )
        os.environ["SCENERY_MANIFESTS_FOLDER"] = f"{scenery_dir}/rehearsal/manifests"
        # Django
        os.environ["SCENERY_TESTED_APP_NAME"] = "some_app"
        os.environ["SCENERY_DB_NAME"] = (
            f"{scenery_dir}/rehearsal/project_django/db.sqlite3"
        )
        os.environ["SCENERY_ROOT_URLCONF"] = (
            "scenery.rehearsal.project_django.project_django.urls"
        )
        os.environ["SCENERY_INSTALLED_APPS"] = (
            "scenery.rehearsal.project_django.some_app"
        )

    ##############
    # CONFIG ENV
    ##############

    # TODO
    # result["config"] = {
    #     "stdlib": None,  # SysConfig.stdlib,
    #     "purelib": None,  # SysConfig.purelib,
    #     "src": None,  # SysConfig.src,
    #     "this_folder": None,  # SysConfig.this_folder,
    # }

    # for key, val in result["config"].items():
    #     logger.debug(f"`{key}` found at {val}")

    #####################
    # CONFIG DJANGO
    #####################

    import scenery.common

    scenery.common.django_setup(
        ROOT_URLCONF=os.getenv("SCENERY_ROOT_URLCONF"),
        APPS=os.getenv("SCENERY_INSTALLED_APPS").split(";"),
        DB_NAME=os.getenv("SCENERY_DB_NAME"),
    )

    # TODO: this should move

    from django.conf import settings

    settings.BLOCK_SOURCE = "markdown"

    from django.urls import get_resolver

    # Print all URL patterns Django is aware of
    resolver = get_resolver()
    for pattern in resolver.url_patterns:
        print("*********************", pattern)

    #############
    # METATESTING
    #############

    # NOTE: the imports will fail if loaded before SCENERY_ENV configuration
    from scenery.metatest import MetaTestRunner, MetaTestDiscoverer

    import scenery.rehearsal

    discoverer = MetaTestDiscoverer()
    tests_discovered = discoverer.discover(
        os.getenv("SCENERY_MANIFESTS_FOLDER"), verbosity=2
    )
    runner = MetaTestRunner()
    result["metatesting"] = runner.run(tests_discovered, args.verbosity)

    ###############
    # OUTPUT RESULT
    ###############

    # TODO : reconsider the correct Way for fucking Git

    # with open("app/tests/views/scenery.json", "w") as f:
    #     json.dump(result, f)


if __name__ == "__main__":

    import sys

    main()
    sys.exit(0)
    # TODO: depends on output actually ?
