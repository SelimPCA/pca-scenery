import unittest
import rehearsal

import django
from django.conf import settings as django_settings

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
    ],
)
django.setup()

# TODO: remove and go through cli only ?

loader = unittest.loader.TestLoader()
runner = unittest.TextTestRunner()
suite = loader.loadTestsFromModule(rehearsal)
runner.run(suite)
