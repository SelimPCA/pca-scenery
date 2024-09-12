import logging

logging.disable(logging.ERROR)

from django.test import TestCase
from django.urls import reverse


from app.models.accounts.user_custom import UserCustom


from app.tests.views._selim_prelim.cases import (
    EMAIL_1,
    PASSWORD_1,
    BIRTH_DATE_VALID_1,
    FIRST_NAME_1,
    LAST_NAME_1,
    CLASS_PREMIERE,
)


class RegisterViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        UserCustom.objects.all().delete()

    def test_register_scenario_0(self):
        """
        [REGISTRATION] Simple user registration [1/2]
        """
        test_data = {
            "first_name": FIRST_NAME_1,
            "last_name": LAST_NAME_1,
            "user_email": EMAIL_1,
            "birth_date_day": "12",
            "birth_date_month": "1",
            "birth_date_year": "1994",
            "class_at_school": CLASS_PREMIERE,
            "password1": PASSWORD_1,
            "password2": PASSWORD_1,
        }

        # TODO : use url mode now
        response = self.client.post(
            reverse("app:register_send_verif_email", kwargs={"send_verif_email": 0}),
            test_data,
        )
        users = list(UserCustom.objects.all())

        self.assertEqual(response.status_code, 302)  # redirection
        self.assertEqual(response.url, "/http_response_for_redirection/")
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, EMAIL_1)
        self.assertEqual(users[0].is_active, False)
        self.assertEqual(users[0].profile.class_at_school, "premiere")

    # def test_register_scenario_1(self):
    #     """
    #     [NO REGISTRATION] Simple user registration : other class [2/2]
    #     """
    #     test_data = {
    #         "first_name": FIRST_NAME_1,
    #         "last_name": LAST_NAME_1,
    #         "user_email": EMAIL_1,
    #         "birth_date_day": "12",
    #         "birth_date_month": "1",
    #         "birth_date_year": "1994",
    #         "class_at_school": CLASS_PREMIERE,
    #         "password1": PASSWORD_1,
    #         "password2": PASSWORD_1,
    #     }

    #     response = self.client.post(
    #         reverse("app:register_send_verif_email", kwargs={"project_id": 4}),
    #         test_data,
    #     )
    #     users = list(UserCustom.objects.all())

    #     self.assertEqual(response.status_code, 302)  # redirection
    #     self.assertEqual(response.url, "/")
    #     self.assertEqual(len(users), 1)
    #     self.assertEqual(users[0].email, "no_mail@mail.com")
    #     self.assertEqual(users[0].is_active, False)
    #     self.assertEqual(users[0].profile.class_at_school, "premiere")

    def test_register_scenario_2(self):
        """
        [NO REGISTRATION] Password only numeric and to common.
        """
        test_data = {
            "first_name": FIRST_NAME_1,
            "last_name": LAST_NAME_1,
            "user_email": EMAIL_1,
            "birth_date_day": "12",
            "birth_date_month": "1",
            "birth_date_year": "1994",
            "class_at_school": CLASS_PREMIERE,
            "password1": "12345678",
            "password2": "12345678",
        }

        response = self.client.post(
            reverse("app:register_send_verif_email", kwargs={"send_verif_email": 0}),
            test_data,
        )
        users = list(UserCustom.objects.all())

        body = str(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(users), 0)
        self.assertIn("Ce mot de passe est trop courant.", body)
        self.assertIn(
            "Ce mot de passe est enti\\xc3\\xa8rement num\\xc3\\xa9rique.", body
        )

    def test_register_scenario_3(self):
        """
        [NO REGISTRATION] Password to common.
        """
        test_data = {
            "first_name": FIRST_NAME_1,
            "last_name": LAST_NAME_1,
            "user_email": EMAIL_1,
            "birth_date_day": "12",
            "birth_date_month": "1",
            "birth_date_year": "1994",
            "class_at_school": CLASS_PREMIERE,
            "password1": "aaaaaaaaa",
            "password2": "aaaaaaaaa",
        }

        response = self.client.post(
            reverse("app:register_send_verif_email", kwargs={"send_verif_email": 0}),
            test_data,
        )
        users = list(UserCustom.objects.all())

        body = str(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(users), 0)
        self.assertIn("Ce mot de passe est trop courant.", body)

    def test_register_scenario_4(self):
        """
        [REGISTRATION]-then-[NO REGISTRATION] Same email (=username).
        """
        test_data = {
            "first_name": FIRST_NAME_1,
            "last_name": LAST_NAME_1,
            "user_email": EMAIL_1,
            "birth_date_day": "12",
            "birth_date_month": "1",
            "birth_date_year": "1994",
            "class_at_school": CLASS_PREMIERE,
            "password1": PASSWORD_1,
            "password2": PASSWORD_1,
        }

        response = self.client.post(
            reverse("app:register_send_verif_email", kwargs={"send_verif_email": 0}),
            test_data,
        )
        users = list(UserCustom.objects.all())

        body = str(response.content)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, EMAIL_1)
        self.assertEqual(users[0].is_active, False)

        test_data = {
            "first_name": FIRST_NAME_1,
            "last_name": LAST_NAME_1,
            "user_email": EMAIL_1,
            "birth_date_day": "12",
            "birth_date_month": "1",
            "birth_date_year": "1994",
            "class_at_school": CLASS_PREMIERE,
            "password1": PASSWORD_1,
            "password2": PASSWORD_1,
        }

        response = self.client.post(
            reverse("app:register_send_verif_email", kwargs={"send_verif_email": 0}),
            test_data,
        )
        users = list(UserCustom.objects.all())

        body = str(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(users), 1)
        self.assertIn(f"email {EMAIL_1}", body)

    def test_register_scenario_5(self):
        """
        [NO REGISTRATION] Date of birth not valid
        """
        test_data = {
            "first_name": FIRST_NAME_1,
            "last_name": LAST_NAME_1,
            "user_email": EMAIL_1,
            "birth_date_day": "30",
            "birth_date_month": "2",
            "birth_date_year": "1994",
            "class_at_school": CLASS_PREMIERE,
            "password1": PASSWORD_1,
            "password2": PASSWORD_1,
        }

        response = self.client.post(
            reverse("app:register_send_verif_email", kwargs={"send_verif_email": 0}),
            test_data,
        )
        users = list(UserCustom.objects.all())

        body = str(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(users), 0)
        self.assertIn("La date de naissance", body)

    def test_register_scenario_6(self):
        """
        [NO REGISTRATION] Younger than 15
        """
        test_data = {
            "first_name": FIRST_NAME_1,
            "last_name": LAST_NAME_1,
            "user_email": EMAIL_1,
            "birth_date_day": "1",
            "birth_date_month": "1",
            "birth_date_year": "2009",
            "class_at_school": CLASS_PREMIERE,
            "password1": PASSWORD_1,
            "password2": PASSWORD_1,
        }

        response = self.client.post(
            reverse("app:register_send_verif_email", kwargs={"send_verif_email": 0}),
            test_data,
        )
        users = list(UserCustom.objects.all())

        body = str(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(users), 0)
        self.assertIn("RGPD", body)

    def test_register_scenario_7(self):
        """
        [REGISTRATION] REGISTER + MAIL
        """
        test_data = {
            "first_name": FIRST_NAME_1,
            "last_name": LAST_NAME_1,
            "user_email": EMAIL_1,
            "birth_date_day": "1",
            "birth_date_month": "1",
            "birth_date_year": "1980",
            "class_at_school": CLASS_PREMIERE,
            "password1": PASSWORD_1,
            "password2": PASSWORD_1,
        }

        response = self.client.post(reverse("app:register"), test_data)
        users = list(UserCustom.objects.all())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/email_verif_confirm/")
        self.assertEqual(len(users), 1)
