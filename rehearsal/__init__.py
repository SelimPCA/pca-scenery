import os
import django
from django.conf import settings as django_settings

###################
# CONFIG
###################
# TODO this should move somewhere else

os.environ["SCENERY_TESTED_APP"] = "some_app"
os.environ["SCENERY_COMMON_ITEMS"] = "rehearsal/common_items.yml"

django_settings.configure(
    ROOT_URLCONF="rehearsal.app_django.app_django.urls",
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        # Add other apps here
        # "rehearsal.app_django.app_django",
        # "rehearsal.app_django.some_app.apps.SomeAppConfig",
        "rehearsal.app_django.some_app",
    ],
)
django.setup()