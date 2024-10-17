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
