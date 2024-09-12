import os

import scenery.common
import scenery.manifest

import yaml
from yaml.constructor import ConstructorError


class ManifestParser:

    # common_items = common.read_yaml("app/tests/views/common_items.yml")
    common_items = scenery.common.read_yaml(os.getenv("SCENERY_COMMON_ITEMS"))

    ################
    # FORMATTED DICT
    ################

    @staticmethod
    def parse_formatted_dict(d: dict):
        """
        Parse a dict with all expected keys:
        - set_up_test_data
        - set_up
        - cases
        - scenes
        - manifest_origin
        """

        d = {key: d[key.value] for key in scenery.manifest.ManifestFormattedDictKeys}
        return scenery.manifest.Manifest.from_formatted_dict(d)

    ##########
    # ANY DICT
    ##########

    @staticmethod
    def validate_dict(d: dict):
        """
        Check only valid keys at top level
        Check either plural or singular is provided for case(s)/ scene(s)
        """

        if not all(
            key in [x.value for x in scenery.manifest.ManifestDictKeys] for key in d.keys()
        ):
            raise ValueError(
                f"Invalid key(s) in {d.keys()} ({d.get('manifest_origin', 'No origin found.')})."
            )

        for key in ["case", "scene"]:

            has_one = key in d
            has_many = f"{key}s" in d

            if has_one and has_many:
                raise ValueError(
                    f"Both `{key}` and `{key}s` keys are present at top level.",
                )

            if not (has_one or has_many):
                raise ValueError(
                    f"Neither `{key}` and `{key}s` keys are present at top level.",
                )

    @staticmethod
    def format_dict(manifest: dict) -> dict:
        """Reformat as dict with expected keys and provide default values if needed"""
        return {
            "set_up_test_data": manifest.get("set_up_test_data", []),
            "set_up": manifest.get("set_up", []),
            "scenes": ManifestParser._format_dict_scenes(manifest),
            "cases": ManifestParser._format_dict_cases(manifest),
            "manifest_origin": manifest["manifest_origin"],
        }

    @staticmethod
    def _format_dict_cases(d: dict) -> dict[str, dict]:
        has_one = "case" in d
        has_many = "cases" in d
        if has_one:
            return {"UNIQUE_CASE": d["case"]}
        elif has_many:
            return d["cases"]

    @staticmethod
    def _format_dict_scenes(d: dict) -> list[dict]:
        has_one = "scene" in d
        has_many = "scenes" in d
        if has_one:
            return [d["scene"]]
        elif has_many:
            return d["scenes"]

    @staticmethod
    def parse_dict(d: dict):
        ManifestParser.validate_dict(d)
        d = ManifestParser.format_dict(d)
        return ManifestParser.parse_formatted_dict(d)

    ##########
    # YAML
    ##########

    # TODO: manifest parser should parse yaml as string,
    # and have a wrapper to read file

    @staticmethod
    def validate_yaml(yaml):
        """
        Check manifest is a dict and keys are expected
        """

        if type(yaml) is not dict:
            raise TypeError(f"Manifest need to be a dict not a '{type(yaml)}'")

        if not all(
            key in [x.value for x in scenery.manifest.ManifestYAMLKeys] for key in yaml.keys()
        ):
            raise ValueError(
                f"Invalid key(s) in {yaml.keys()} ({yaml.get('origin', 'No origin found.')})"
            )

    # @staticmethod
    # def parse_yaml(filename):
    #     d = read_yaml(filename)
    #     ManifestParser.validate_yaml(d)
    #     d["manifest_origin"] = d.get("manifest_origin", filename)
    #     if "variables" in d:
    #         del d["variables"]
    #     return ManifestParser.parse_dict(d)

    @staticmethod
    def _yaml_constructor_case(loader: yaml.SafeLoader, node: yaml.nodes.Node):
        if isinstance(node, yaml.nodes.ScalarNode):
            return scenery.manifest.Substituable(loader.construct_scalar(node))
        else:
            raise ConstructorError

    @staticmethod
    def _yaml_constructor_common_item(loader: yaml.SafeLoader, node: yaml.nodes.Node):

        if isinstance(node, yaml.nodes.ScalarNode):
            return ManifestParser.common_items[loader.construct_scalar(node)]
        if isinstance(node, yaml.nodes.MappingNode):
            d = loader.construct_mapping(node)
            case = ManifestParser.common_items[d["ID"]] | {
                key: value for key, value in d.items() if key != "ID"
            }
            return case
        else:
            raise ConstructorError

    @staticmethod
    def read_manifest_yaml(fn):
        """A function to read YAML file with custom tags"""

        # NOTE: inspired by https://matthewpburruss.com/post/yaml/
        # TODO: loader should be a class attribute

        # Add constructor
        # Loader = yaml.SafeLoader
        Loader = yaml.FullLoader
        Loader.add_constructor("!case", ManifestParser._yaml_constructor_case)
        Loader.add_constructor(
            "!common-item", ManifestParser._yaml_constructor_common_item
        )

        with open(fn) as f:
            content = yaml.load(f, Loader)


        return content

    @staticmethod
    def parse_yaml(filename):
        d = ManifestParser.read_manifest_yaml(filename)
        ManifestParser.validate_yaml(d)
        d["manifest_origin"] = d.get("manifest_origin", filename)
        if "variables" in d:
            del d["variables"]
        return ManifestParser.parse_dict(d)

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
