import argparse
import os
import logging
import importlib.util


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
        "-s",
        "--settings",
        dest="settings_module",
        type=str,
        default=None,
        help="Location of django settings module",
    )

    # parser.add_argument(
    #     "--view",
    #     dest="restrict_view_name",
    #     action="store",
    #     default=None,
    #     help="Restrict to a specific view",
    # )

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

    # import dotenv

    # has_config = dotenv.load_dotenv(".env_scenery")
    has_config = os.path.exists("./scenery_settings.py")
    if has_config:
        # TODO this should be a function ?
        # scenery_settings = importlib.import_module("./scenery_settings.py")
        spec = importlib.util.spec_from_file_location(
            "scenery_settings", "./scenery_settings.py"
        )
        scenery_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scenery_settings)

        os.environ["SCENERY_COMMON_ITEMS"] = scenery_settings.SCENERY_COMMON_ITEMS
        os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = (
            scenery_settings.SCENERY_SET_UP_INSTRUCTIONS
        )

        # SCENERY_DB = scenery_settings.SCENERY_DB
        # SCENERY_ROOT_URLCONF = scenery_settings.SCENERY_ROOT_URLCONF
        # SCENERY_INSTALLED_APPS = scenery_settings.SCENERY_INSTALLED_APPS
        SCENERY_MANIFESTS_FOLDER = scenery_settings.SCENERY_MANIFESTS_FOLDER
        # SCENERY_MIDDLEWARE = scenery_settings.SCENERY_MIDDLEWARE

        # from pprint import pprint

        # print("*****************")
        # pprint(SCENERY_MIDDLEWARE)

    else:
        # TODO: this should actually become a test
        scenery_dir = os.path.abspath(os.path.join(__file__, os.pardir))

        # Scenery
        os.environ["SCENERY_COMMON_ITEMS"] = f"{scenery_dir}/rehearsal/common_items.yml"
        os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = (
            "scenery.rehearsal.set_up_instructions"
        )
        # os.environ["SCENERY_MANIFESTS_FOLDER"] = f"{scenery_dir}/rehearsal/manifests"
        # Django
        os.environ["SCENERY_TESTED_APP_NAME"] = "some_app"

        # SCENERY_DB = {
        #     "ENGINE": "django.db.backends.sqlite3",
        #     "NAME": "scenery/rehearsal/project_django/db.sqlite3",
        # }
        # SCENERY_ROOT_URLCONF = "scenery.rehearsal.project_django.project_django.urls"
        # SCENERY_INSTALLED_APPS = ["scenery.rehearsal.project_django.some_app"]
        SCENERY_MANIFESTS_FOLDER = f"{scenery_dir}/rehearsal/manifests"
        # SCENERY_MIDDLEWARE = []

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

    # scenery.common.django_setup(
    #     ROOT_URLCONF=SCENERY_ROOT_URLCONF,
    #     APPS=SCENERY_INSTALLED_APPS,
    #     DB_DICT=SCENERY_DB,
    #     MIDDLEWARE=SCENERY_MIDDLEWARE,
    # )

    scenery.common.django_setup(settings_module=args.settings_module)

    # from pprint import pprint
    # print("##################")
    # pprint(SCENERY_DB)

    from django.conf import settings, global_settings

    # # Print out the settings to debug
    # print("INSTALLED_APPS:", settings.INSTALLED_APPS)
    # print("DATABASES:", settings.DATABASES)
    # print("MIDDLEWARE:", settings.MIDDLEWARE)
    # print("ROOT_URLCONF:", settings.ROOT_URLCONF)
    # print("DEBUG:", settings.DEBUG)

    # TODO: this should move outside of pca-scenery

    settings.BLOCK_SOURCE = "markdown"
    # global_settings.BLOCK_SOURCE = "markdown"
    #
    # Print all URL patterns Django is aware of
    # from django.urls import get_resolver

    # resolver = get_resolver()
    # for pattern in resolver.url_patterns:
    #     print("*********************", pattern)

    #############
    # METATESTING
    #############

    # NOTE: the imports will fail if loaded before SCENERY_ENV configuration
    from scenery.metatest import MetaTestRunner, MetaTestDiscoverer

    import scenery.rehearsal

    discoverer = MetaTestDiscoverer()
    tests_discovered = discoverer.discover(SCENERY_MANIFESTS_FOLDER, verbosity=2)
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
