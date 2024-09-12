"""Test the package `scenery` itself."""



def main():

    ###################
    # CONFIG ENV
    ###################

    import os

    os.environ["SCENERY_TESTED_APP"] = "some_app"
    os.environ["SCENERY_COMMON_ITEMS"] = "scenery/rehearsal/common_items.yml"
    os.environ["SCENERY_SET_UP_INSTRUCTIONS"] = "scenery.rehearsal.set_up_instructions"

    ###################
    # CONFIG DJANGO
    ###################

    import django
    from django.conf import settings as django_settings
    # from django.apps import apps as django_apps

    django_settings.configure(
        ROOT_URLCONF="scenery.rehearsal.project_django.project_django.urls",
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            # Add other apps here
            "scenery.rehearsal.project_django.some_app",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "scenery/rehearsal/project_django/db.sqlite3",
            }
        },
    )
    django.setup()

    #############
    # RUN TESTS
    #############

    import scenery.rehearsal

    discoverer = scenery.rehearsal.RehearsalDiscoverer()
    runner = scenery.rehearsal.RehearsalRunner()
    tests_discovered = discoverer.discover(verbosity=2)
    runner.run(tests_discovered, verbosity=2)



if __name__ == "__main__":
    main()
