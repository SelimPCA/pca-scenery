import datetime

# Django
from django.db.models.deletion import ProtectedError
from django.apps import apps

# Models
from app.models.accounts.profile import Profile
from app.models.accounts.user_custom import UserCustom

# Commands
from app.management.commands.load_highschool_france import LoadHSCommand
from app.management.commands.createsuperusercustom import (
    Command as CreateSuperUserCustomCommand,
)


def reset_db():
    """Delete all instances of all app models"""
    # TODO: one clean to do it could be to use topolocial sorting?
    app_config = apps.get_app_config("app")
    # NOTE bug if kept as a iterator, UserCustom cannot be deleted
    models = list(app_config.get_models())

    from django.db import connections

    # Print the database alias and connection details

    db_alias = models[0].objects.all().db
    connection = connections[db_alias]
    # print(connections)

    # print(f"Database Alias: {db_alias}")
    # print(f"Database Name: {connection.settings_dict['NAME']}")
    # print(f"Database Engine: {connection.settings_dict['ENGINE']}")
    # print(f"User: {connection.settings_dict['USER']}")
    # print(f"Host: {connection.settings_dict['HOST']}")
    while any(model.objects.exists() for model in models):
        for model in models:
            try:
                model.objects.all().delete()
            except ProtectedError:
                continue
            except:
                raise
    # for model in models:
    #     print(model)
    #     print(len(model.objects.all()))
    #     print("\n\n")


def load_higshcools():
    """Load highscool data"""
    lhsc = LoadHSCommand()
    lhsc.handle()


def create_superuser():
    """Create a super user"""
    csucc = CreateSuperUserCustomCommand()
    csucc.handle()


def create_testuser(
    *,
    user_email,
    first_name,
    last_name,
    password,
    is_active,
    birth_date_year,
    birth_date_month,
    birth_date_day,
    class_at_school,
    contract,
):
    """Create a test user"""

    birth_date = datetime.datetime(birth_date_year, birth_date_month, birth_date_day)

    user = UserCustom(
        username=user_email,
        email=user_email,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
    )
    user.set_password(password)

    user.save()

    profile = Profile(
        user=user,
        birth_date=birth_date,
        class_at_school=class_at_school,
        contract=contract,
    )
    profile.save()

    return user


def login(
    client,
    *,
    user_email,
    password,
):
    """Login a test user"""
    client.login(username=user_email, password=password)
