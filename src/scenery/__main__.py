import argparse
import logging


def main():

    result = {}

    #################
    # PARSE ARGUMENTS
    #################

    # TODO: do I really want defaults for settings module ?

    parser = argparse.ArgumentParser()

    # TODO: I should be able to take <manifest>.*.<scene>
    parser.add_argument(
        "restrict",
        nargs="?",
        default=None,
        help="Optional test restriction <manifest>.<case>.<scene>",
    )

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
        "--scenery_settings",
        dest="scenery_settings_module",
        type=str,
        default="scenery_settings",
        help="Location of scenery settings module",
    )

    parser.add_argument(
        "-ds",
        "--django_settings",
        dest="django_settings_module",
        type=str,
        default=None,
        help="Location of django settings module",
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

    # logger_app = logging.getLogger("logger_app")  # TODO: change? should be in env ?
    # logger_app.handlers = []
    # logger_app.addHandler(handler_full)
    # logger_app.setLevel(level)

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

    ##################
    # CONFIG SCENERY
    ##################

    import scenery.common

    scenery.common.scenery_setup(settings_location=args.scenery_settings_module)

    #####################
    # CONFIG DJANGO
    #####################

    scenery.common.django_setup(settings_module=args.django_settings_module)

    # TODO: I think selim checked something related to this
    # from django.conf import settings
    # settings.BLOCK_SOURCE = "markdown"

    #############
    # METATESTING
    #############

    # NOTE: the imports will fail if loaded before SCENERY_ENV configuration
    from scenery.metatest import MetaTestRunner, MetaTestDiscoverer

    discoverer = MetaTestDiscoverer()
    tests_discovered = discoverer.discover(verbosity=2, restrict=args.restrict)
    runner = MetaTestRunner()
    result["metatesting"] = runner.run(tests_discovered, args.verbosity)

    ###############
    # OUTPUT RESULT
    ###############

    # TODO

    # with open("app/tests/views/scenery.json", "w") as f:
    #     json.dump(result, f)


if __name__ == "__main__":

    import sys

    main()
    sys.exit(0)
    # TODO: depends on output actually
