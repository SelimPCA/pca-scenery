# MANIFEST PARSER
#################

# @staticmethod
# def remind_origin(func):
#     """This will be useful when we will dynamically generate manifests"""

#     def wrapper(d):
#         try:
#             return func(d)
#         except Exception as e:
#             if isinstance(d, dict):
#                 e.add_note(
#                     f"\nManifest origin:{d.get('origin', 'No origin found.')}"
#                 )
#             raise

#     return wrapper


# def factory_yaml_constructor(cls: type):
#     """Build the yaml constructor for a given class"""

#     def constructor(loader: yaml.SafeLoader, node: yaml.nodes.Node):
#         """Construct the required class"""
#         # print("!!!!!!!!!!!", node)
#         if isinstance(node, yaml.nodes.MappingNode):
#             # return cls(**loader.construct_mapping(node))
#             return cls(**loader.construct_mapping(node, deep=True))
#         elif isinstance(node, yaml.nodes.ScalarNode):
#             return cls(loader.construct_scalar(node))
#         else:
#             raise NotImplementedError(f"Yaml custom tag for node of type {type(node)}.")

#     return constructor

####################
# SYSTEM CONFIG
####################

import os
import sysconfig


class SysConfig:

    stdlib = sysconfig.get_paths()["stdlib"]
    purelib = sysconfig.get_paths()["purelib"]
    this_folder = __package__.replace(".", "/")
    src = os.path.abspath(__file__)
    src = src.replace(f"/{this_folder}/__init__.py", "")

    def __new__(cls):
        raise TypeError("SysConfig cannot be instantiated")


####################
# ENV CONFIG
####################


# from app.tests.utils import load_dotenv
# To avoid to store any credential
# load_dotenv(dotenv_path=f"{SysConfig.src}/{SysConfig.this_folder}/.env_scenery")

# print(f"{SysConfig.src}/{SysConfig.this_folder}/.env_scenery")
# print(os.getenv("SCENERY_TESTING_EMAIL"))
# print(os.getenv("SCENERY_TESTING_PASSWORD"))


def main():

    result = {}

    #################
    # PARSE ARGUMENTS
    #################

    import argparse

    parser = argparse.ArgumentParser()

    choices_coverage = ["testcase", "test", "function", "statement", "branch"]

    def coverage_args_as_kwargs(l):
        """
        This is actually applied not as type argument of parser.add_argument
        as this would uselessly increase the number of choices, which would be required
        to be generated by itertools
        """
        nonlocal choices_coverage
        if "all" in l:
            d = {key: True for key in choices_coverage}
        else:
            d = {key: key in l for key in choices_coverage}
        return d


# Print all URL patterns Django is aware of
# from django.urls import get_resolver

# resolver = get_resolver()
# for pattern in resolver.url_patterns:
#     print("*********************", pattern)


def graph_bar(d: dict, scale=20):
    """
    Returns an ASCII graph bar for a dictionary of values between 0 and 1.

    Args:
        d (dict): A dictionary with values between 0 and 1.
        scale (int, optional): The width of the graph bar. Defaults to 20.

    Returns:
        dict: A dictionary with the same keys as the input, but values replaced by ASCII graph bars.
    """
    # bars = {key: (val, 1 - val) for key, val in d.items()}
    bars = {key: (floor(scale * x), scale - floor(scale * x)) for key, x in d.items()}
    bars = {
        key: str(colorize("green", "=" * x)) + str(colorize("red", "=" * y))
        for key, (x, y) in bars.items()
    }

    bars = {key: bar + f"|{int(100 * d[key])} %" for key, bar in bars.items()}
    # bars = {key: bar.ljust(20) + f"|{round(d[key], 2)}" for key, bar in bars.items()}
    return bars