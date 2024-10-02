from typing import Any

from django.test import TestCase
from django.http import HttpResponse, HttpResponseRedirect
from django.apps import apps
from django.db.models.deletion import ProtectedError

from app.tests.views.dataclasses import HttpCheck
from app.tests.views.enums import DirectiveCommand, DomArgument


from bs4 import BeautifulSoup


class HttpChecker:

    @staticmethod
    def exec_check(django_testcase: TestCase, response: HttpResponse, check: HttpCheck):

        ## SANITY CHECK SELIM
        ## TO CHECK IN THE DATABASE ON TEST ENVIRONMENT THAT SOMETHING HAS BEEN STORED
        ## PROBABLY WE SHOULD AT IT AT THE LEVEL OF THE SCENERY

        app_config = apps.get_app_config("app")
        # !!! bug if kept as a iterator, UserCustom cannot be deleted
        models = list(app_config.get_models())

        for model in models:
            try:
                record_count = model.objects.count()
                # print("#" * 10)
                # print("SELIM SANITY CHECK DB SCALINGO CORRECTLY CONNECTED")
                # print(model)
                # print(record_count, "objects")
                # print("\n")
            except ProtectedError:
                continue
            except:
                raise

        match check.instruction:
            case DirectiveCommand.STATUS_CODE:
                HttpChecker.check_status_code(django_testcase, response, check.args)
            case DirectiveCommand.REDIRECT_URL:
                HttpChecker.check_redirect_url(django_testcase, response, check.args)
            case DirectiveCommand.COUNT_INSTANCES:
                HttpChecker.check_count_instances(django_testcase, response, check.args)
            case DirectiveCommand.DOM_ELEMENT:
                HttpChecker.check_dom_element(django_testcase, response, check.args)
            case _:
                raise NotImplementedError(check)

    @staticmethod
    def check_status_code(django_testcase: TestCase, response: HttpResponse, args: int):
        django_testcase.assertEqual(response.status_code, args)

    @staticmethod
    def check_redirect_url(self: TestCase, response: HttpResponseRedirect, args: str):
        self.assertEqual(response.url, args)

    @staticmethod
    def check_count_instances(
        django_testcase: TestCase, response: HttpResponse, args: dict
    ):
        # cls = apps.get_model("app", args["model"])
        # instances = list(cls.objects.all())
        instances = list(args["model"].objects.all())
        django_testcase.assertEqual(len(instances), args["n"])

    @staticmethod
    def check_dom_element(
        django_testcase: TestCase, response: HttpResponse, args: dict[DomArgument, Any]
    ):
        # NOTE: we do not support xpath as it is not supported by BeautifulSoup
        # this would require to use lxml
        # TODO: count number of elements from find_all

        soup = BeautifulSoup(response.content, "html.parser")

        # Apply the scope
        if scope := args.get(DomArgument.SCOPE):
            soup = soup.find(**scope)

        # Locate the element(s)
        # If find_all is provided, the checks are performed on ALL elements
        # If find is provided we enforce the result to be la list
        if args.get(DomArgument.FIND_ALL):
            dom_elements = soup.find_all(**args[DomArgument.FIND_ALL])
            django_testcase.assertGreaterEqual(len(dom_elements), 1)
        elif args.get(DomArgument.FIND):
            dom_element = soup.find(**args[DomArgument.FIND])
            django_testcase.assertIsNotNone(dom_element)
            dom_elements = [dom_element]
        else:
            raise ValueError("Neither find of find_all argument provided")

        # Perform the additional checks
        if count := args.get(DomArgument.COUNT):
            django_testcase.assertEqual(len(dom_elements), count)
        for dom_element in dom_elements:
            if text := args.get(DomArgument.TEXT):
                # TODO: this should/could disappear as text is too likely to change
                django_testcase.assertEqual(dom_element.text, text)
            if attribute := args.get(DomArgument.ATTRIBUTE):
                # TODO: this should move to manifest parser
                match attribute["value"]:
                    case str(v) | list(v):
                        pass
                    case int(n):
                        attribute["value"] = str(n)
                    case x:
                        raise ValueError(
                            f"attribute value can only by `str` or `list[str]` not '{type(x)}'"
                        )

                # print("HERE", dom_element[attribute["name"]], attribute["value"])
                # print(dom_element)
                django_testcase.assertEqual(
                    dom_element[attribute["name"]], attribute["value"]
                )
