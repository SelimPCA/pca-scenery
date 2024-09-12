import datetime
import json
import logging

# logging.disable(logging.ERROR)

from django.test import TestCase
from django.urls import reverse

from app.management.commands.createsuperusercustom import (
    Command as CreateSuperUserCustomCommand,
    EMAIL_SUPERUSER,
    PASSWORD_SUPERUSER,
)
from app.models.accounts.user_custom import UserCustom
from app.models.accounts.profile import Profile
from app.models.v1.enums import ClassAtSchoolSelectable


# ?? useful? OLD
from app.tests.views._prelim_selim.cases import (
    EMAIL_1,
    PASSWORD_1,
    BIRTH_DATE_VALID_1,
    FIRST_NAME_1,
    LAST_NAME_1,
    CLASS_PREMIERE,
)


from app.tests.utils import create_testuser


class UserAnswerViewTest(TestCase):
    # Only once
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    # Only once ? see below
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        UserCustom.objects.all().delete()

    def test_login_scenario_0(self):
        """
        [PASS] Login super user
        """

        csucc = CreateSuperUserCustomCommand()
        csucc.handle()

        superuser = UserCustom.objects.first()

        test_data = {
            "user_email": EMAIL_SUPERUSER,
            "password": PASSWORD_SUPERUSER,
        }

        response = self.client.post(reverse("app:login"), test_data)
        users = list(UserCustom.objects.all())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, f"/class/{superuser.profile.class_at_school}/chapters"
        )
        self.assertEqual(len(users), 1)

    def test_login_scenario_1(self):
        """
        [PASS] Login normal active user
        """

        user = create_testuser(
            username=EMAIL_1,
            email=EMAIL_1,
            first_name=FIRST_NAME_1,
            last_name=LAST_NAME_1,
            password=PASSWORD_1,
            is_active=True,
            birth_date=BIRTH_DATE_VALID_1,
            class_at_school=CLASS_PREMIERE,
            contract=0,
        )

        test_data = {
            "user_email": EMAIL_1,
            "password": PASSWORD_1,
        }

        response = self.client.post(reverse("app:login"), test_data)
        users = list(UserCustom.objects.all())

        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            response.url, f"/class/{user.profile.class_at_school}/chapters"
        )
        self.assertEqual(users[0].email, EMAIL_1)
        self.assertEqual(users[0].is_active, True)

    def test_login_scenario_2(self):
        """
        [PASS] Login normal non active user
        """

        user = create_testuser(
            username=EMAIL_1,
            email=EMAIL_1,
            first_name=FIRST_NAME_1,
            last_name=LAST_NAME_1,
            password=PASSWORD_1,
            is_active=False,
            birth_date=BIRTH_DATE_VALID_1,
            class_at_school=CLASS_PREMIERE,
            contract=0,
        )

        test_data = {
            "user_email": EMAIL_1,
            "password": PASSWORD_1,
        }

        response = self.client.post(reverse("app:login"), test_data)
        users = list(UserCustom.objects.all())

        self.assertEqual(response.url, "/email_verif_confirm/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(users[0].email, EMAIL_1)
        self.assertEqual(users[0].is_active, False)

    def test_login_scenario_3(self):
        """
        [ERROR] Login normal non active user: wrong password
        """

        user = create_testuser(
            username=EMAIL_1,
            email=EMAIL_1,
            first_name=FIRST_NAME_1,
            last_name=LAST_NAME_1,
            password=PASSWORD_1,
            is_active=False,  ##################### !!!!
            birth_date=BIRTH_DATE_VALID_1,
            class_at_school=CLASS_PREMIERE,
            contract=0,
        )

        test_data = {
            "user_email": EMAIL_1,
            "password": PASSWORD_1 + "some_other_string",
        }

        response = self.client.post(reverse("app:login"), test_data)

        users = list(UserCustom.objects.all())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/email_verif_confirm/")

    def test_login_scenario_4(self):
        """
        [ERROR] Login normal active user : wrong password
        """

        user = create_testuser(
            username=EMAIL_1,
            email=EMAIL_1,
            first_name=FIRST_NAME_1,
            last_name=LAST_NAME_1,
            password=PASSWORD_1,
            is_active=True,  ##################### !!!!
            birth_date=BIRTH_DATE_VALID_1,
            class_at_school=CLASS_PREMIERE,
            contract=0,
        )
        test_data = {
            "user_email": EMAIL_1,
            "password": PASSWORD_1 + "some_other_string",
        }
        response = self.client.post(reverse("app:login"), test_data)

        users = list(UserCustom.objects.all())
        self.assertEqual(response.status_code, 401)

    def test_login_scenario_5(self):
        """
        [ERROR] Login normal for non existing user
        """

        test_data = {"user_email": EMAIL_1, "password": PASSWORD_1}
        response = self.client.post(reverse("app:login"), test_data)
        users = list(UserCustom.objects.all())
        self.assertEqual(response.status_code, 401)

        # self.assertEqual(response.url, "/email_verif_confirm/")
        # self.assertEqual(response.status_code, 302)
        # self.assertEqual(users[0].email, EMAIL)
        # self.assertEqual(users[0].is_active, False)
