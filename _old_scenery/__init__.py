"""Scenery package"""

import os
import sysconfig


####################
# DJANGO CONFIG
####################

# Config django, otherwise imports from app fail
import django


from app.email.backend_sib import EmailBackendSib


if os.environ.get("ENV") == "PRODUCTION":
    api_response, success = EmailBackendSib.send_mail(
        html_msg="TENTATIVE OF RUNNING TESTS INTO PRODUCTION",
        subject="TENTATIVE OF RUNNING TESTS INTO PRODUCTION",
        dest_email_list=["ssfmh@pm.me", "etienne.madinier@proton.me"],
        # dest_name=user.first_name,
        # sender_name=self.sender_name,
        sender_email="ne-pas-repondre@admin.pointcarre.app",
    )
    print("success", success)
    print(api_response)
    raise ValueError("PRODUCTION SHOULD NEVER RUN TESTS DIRECTLY")


elif os.environ.get("ENV") is None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pca.settings.local")


elif os.environ.get("ENV") == "TEST":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pca.settings.test")


else:
    raise ImportError("Cannot configure django properly")
django.setup()


# Fuck : mandatory string
# Todo : think about it :
# Doit on vraiment faire le export MODE_SCENERY ?
os.environ.update({"MODE_SCENERY": "1"})


from django.conf import settings

# After django setup
BLOCK_SOURCE = settings.BLOCK_SOURCE
if BLOCK_SOURCE != "markdown":
    raise ValueError(f"BLOCK_SOURCE={BLOCK_SOURCE} AND MUST BE EQUAL TO `markdown`")


# def update_env(scalingo_variables):
#     _environ = dict(os.environ)  # or os.environ.copy()
#     print(len(_environ))

#     try:
#         for var_dict in scalingo_variables:
#             _environ[var_dict["name"]] = var_dict["value"]

#         # Correct alias database url ($SCALINGO_POSTGRESQL_URL for now)
#         _environ["DATABASE_URL"] = _environ["SCALINGO_POSTGRESQL_URL"]

#     except Exception as e:
#         print(e)

#     finally:
#         os.environ.clear()
#         os.environ.update(_environ)


# from app.tests.utils import load_dotenv

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

# Todo : doesn't work
# To avoid to store any credential
# load_dotenv(dotenv_path=f"{SysConfig.src}/{SysConfig.this_folder}/.env_scenery")

# print(f"{SysConfig.src}/{SysConfig.this_folder}/.env_scenery")
# print(os.getenv("SCENERY_TESTING_EMAIL"))
# print(os.getenv("SCENERY_TESTING_PASSWORD"))


####################
# DJANGO CONFIG
####################

# Config django, otherwise imports from app fail
# import django

# TODO: how it will work on scalingo (see "test.sh")
# TODO: this shoudlbecome a function

# if env := os.environ.get("ENV") is None:
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pca.settings.local")
# else:
#     raise ImportError(f"Cannot configure django properly in scenery for ENV={env}")
# django.setup()
