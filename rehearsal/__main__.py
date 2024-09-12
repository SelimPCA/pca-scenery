"""Test the package `pca-scenery` itself."""

import os

import pca_scenery.rehearsal


###################
# CONFIG DJANGO
###################

import django
from django.conf import settings as django_settings
from django.apps import apps as django_apps

django_settings.configure(
    ROOT_URLCONF="rehearsal.project_django.project_django.urls",
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        # Add other apps here
        "rehearsal.project_django.some_app",
    ],
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "rehearsal/project_django/db.sqlite3",
        }
    },
)
django.setup()


###################
# CONFIG ENV
###################


def main():
    os.environ["SCENERY_TESTED_APP"] = "some_app"
    os.environ["SCENERY_COMMON_ITEMS"] = "rehearsal/common_items.yml"
    os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = "rehearsal.set_up_instructions"

    discoverer = pca_scenery.rehearsal.RehearsalDiscoverer()
    runner = pca_scenery.rehearsal.RehearsalRunner()
    tests_discovered = discoverer.discover(verbosity=2)
    runner.run(tests_discovered, verbosity=2)


if __name__ == "__main__":
    main()
