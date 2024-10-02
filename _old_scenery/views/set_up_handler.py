import datetime
import logging

# Django
from django.db.models.deletion import ProtectedError
from django.apps import apps

# Tests
from app.tests.views.enums import SetUpCommand

# Models
from app.models.accounts.profile import Profile
from app.models.accounts.user_custom import UserCustom

# Commands
from app.management.commands.load_highschool_france import LoadHSCommand
from app.management.commands.createsuperusercustom import (
    Command as CreateSuperUserCustomCommand,
)

# TODO: the import will be replaced by the new version of it once we load the .md files within the DB
# from app.management.commands.load_content_custom import Command as LoadContentCommand (OBSOlETE)


# class TestUserSettings:
#     valid_email = "ssfmh@pm.me"
#     password = "tXo8A5V5QJTvpwnNRAKX"
#     first_name = "Harry"
#     last_name = "Potter"
#     birth_year = 1980
#     birth_month = 7
#     birth_day = 31
#     class_at_school = "premiere"
#     is_active = True
#     contract = 0


class SetUpHandler:
    """
    Responsible for executing instructions used in `TestCase.setUp` and `TestCase.setUpTestData`
    provided in the manifest.
    In practice, the MethodBuilder will build functions that use the SetUpHandler to execute
    `SetUpInstruction`
    """

    @staticmethod
    def exec_set_up_instruction(client, instruction: SetUpCommand):
        """Execute the method corresponding to the SetUpInstruction"""

        match instruction.command, instruction.args:
            case SetUpCommand.RESET_DB, {}:
                SetUpHandler.reset_db()
            case SetUpCommand.CREATE_SUPERUSER, {}:
                SetUpHandler.create_superuser()
            # case SetUpCommand.CREATE_TESTUSER, {}:
            #     SetUpHandler.create_testuser()
            # case SingleKeyDict(_dict={SetUpCommand.CREATE_TESTUSER: kwargs}):
            case SetUpCommand.CREATE_TESTUSER, dict(kwargs):
                SetUpHandler.create_testuser(**kwargs)
            case SetUpCommand.LOGIN, dict(kwargs):
                SetUpHandler.login(client, **kwargs)
            case SetUpCommand.LOAD_HIGHSCHOOLS, {}:
                SetUpHandler.load_higshcools()
            case _:
                raise NotImplementedError(instruction)

        logger = logging.getLogger(__package__)
        logger.debug(f"Applied {instruction}")

    @staticmethod
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

    @staticmethod
    def load_higshcools():
        """Load highscool data"""
        lhsc = LoadHSCommand()
        lhsc.handle()

    @staticmethod
    def create_superuser():
        """Create a super user"""
        csucc = CreateSuperUserCustomCommand()
        csucc.handle()

    @staticmethod
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

        birth_date = datetime.datetime(
            birth_date_year, birth_date_month, birth_date_day
        )

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

    @staticmethod
    def login(
        client,
        *,
        user_email,
        password,
    ):
        """Login a test user"""
        client.login(username=user_email, password=password)
