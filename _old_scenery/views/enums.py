from enum import Enum


####################
# MANIFEST TOP LEVEL
####################


class ManifestFormattedDictKeys(Enum):
    """Used in formated dict, they are exactly contained when passed in Manifest.from_formatted_dict"""

    SET_UP_TEST_DATA = "set_up_test_data"
    SET_UP = "set_up"
    CASES = "cases"
    SCENES = "scenes"
    MANIFEST_ORIGIN = "manifest_origin"


class ManifestDictKeys(Enum):
    """Keys allowed for Manifest.from_dict (and .from_yaml)"""

    SET_UP_TEST_DATA = "set_up_test_data"
    SET_UP = "set_up"
    CASES = "cases"
    SCENES = "scenes"
    MANIFEST_ORIGIN = "manifest_origin"

    CASE = "case"
    SCENE = "scene"


class ManifestYAMLKeys(Enum):
    """Keys allowed for Manifest.from_yaml compared to Manifest.from_dict"""

    SET_UP_TEST_DATA = "set_up_test_data"
    SET_UP = "set_up"
    CASES = "cases"
    SCENES = "scenes"
    MANIFEST_ORIGIN = "manifest_origin"

    CASE = "case"
    SCENE = "scene"

    VARIABLES = "variables"


########
# SET UP
########


class SetUpCommand(Enum):
    """Values allowed in Manifest["set_up"] and Manifest["set_up_test_data"]"""

    RESET_DB = "reset_db"
    CREATE_SUPERUSER = "create_superuser"
    CREATE_TESTUSER = "create_testuser"
    LOGIN = "login"
    LOAD_HIGHSCHOOLS = "load_highschools"
    # LOAD_CONTENT = "load_content"


##############
# SUBSTITUTION
##############


# class HttpTarget(Enum):
#     DATA = "data"
#     CHECKS = "checks"
#     URL_PARAMETERS = "url_parameters"


########
# CHECKS
########


class DirectiveCommand(Enum):
    """Values allowed for Manifest["checks"]"""

    STATUS_CODE = "status_code"
    REDIRECT_URL = "redirect_url"
    COUNT_INSTANCES = "count_instances"
    DOM_ELEMENT = "dom_element"


class DomArgument(Enum):
    """Values allowed for Manifest["checks]["dom_element"]"""

    FIND = "find"
    FIND_ALL = "find_all"
    COUNT = "count"
    SCOPE = "scope"
    TEXT = "text"
    ATTRIBUTE = "attribute"
