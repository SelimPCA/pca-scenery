import os

from django.apps import apps as django_apps
from django.db.models.deletion import ProtectedError

from rehearsal.project_django.some_app.models import SomeModel

def reset_db():
    """Delete all instances of all app models"""

    app_config = django_apps.get_app_config(os.getenv("SCENERY_TESTED_APP"))
    # NOTE bug if kept as an iterator, UserCustom cannot be deleted
    models = list(app_config.get_models())

    while any(model.objects.exists() for model in models):
        for model in models:
            try:
                model.objects.all().delete()
            except ProtectedError:
                continue
            except:
                raise


def login(
    client,
    *,
    user_email,
    password,
):
    """Login a test user"""
    client.login(username=user_email, password=password)

# TODO: all of this below should be in a file in the app and set_up_handler should define its method dynamically

def create_someinstance(*,some_field):

    SomeModel(some_field=some_field)
    # birth_date = datetime.datetime(
    #     birth_date_year, birth_date_month, birth_date_day
    # )

    # user = UserCustom(
    #     username=user_email,
    #     email=user_email,
    #     first_name=first_name,
    #     last_name=last_name,
    #     is_active=is_active,
    # )
    # user.set_password(password)

    # user.save()

    # profile = Profile(
    #     user=user,
    #     birth_date=birth_date,
    #     class_at_school=class_at_school,
    #     contract=contract,
    # )
    # profile.save()

    # return user

