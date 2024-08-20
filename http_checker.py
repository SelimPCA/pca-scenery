import http
from typing import Any

import manifest

import django.test
import django.http
# from django.test import TestCase
# from django.http import HttpResponse, HttpResponseRedirect
from django.apps import apps as django_apps
from django.db.models.deletion import ProtectedError

from bs4 import BeautifulSoup


class HttpChecker:


    @staticmethod
    def get_http_client_response(client, take: manifest.HttpTake):

        # print("###########", take)

        match take.method:
            case http.HTTPMethod.GET:
                response = client.get(
                    take.url,
                    take.data,
                )
            case http.HTTPMethod.POST:
                response = client.post(
                    take.url,
                    take.data,
                )
            case _:
                raise NotImplementedError(take.method)
        return response


    @staticmethod
    def exec_check(django_testcase: django.test.TestCase, response: django.http.HttpResponse, check: manifest.HttpCheck):

        ## SANITY CHECK SELIM
        ## TO CHECK IN THE DATABASE ON TEST ENVIRONMENT THAT SOMETHING HAS BEEN STORED
        ## PROBABLY WE SHOULD AT IT AT THE LEVEL OF THE SCENERY

        app_config = django_apps.get_app_config("app")
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
            case manifest.DirectiveCommand.STATUS_CODE:
                HttpChecker.check_status_code(django_testcase, response, check.args)
            case manifest.DirectiveCommand.REDIRECT_URL:
                HttpChecker.check_redirect_url(django_testcase, response, check.args)
            case manifest.DirectiveCommand.COUNT_INSTANCES:
                HttpChecker.check_count_instances(django_testcase, response, check.args)
            case manifest.DirectiveCommand.DOM_ELEMENT:
                HttpChecker.check_dom_element(django_testcase, response, check.args)
            case _:
                raise NotImplementedError(check)

    @staticmethod
    def check_status_code(django_testcase: django.test.TestCase, response: django.http.HttpResponse, args: int):
        django_testcase.assertEqual(response.status_code, args)

    @staticmethod
    def check_redirect_url(self: django.test.TestCase, response: django.http.HttpResponseRedirect, args: str):
        self.assertEqual(response.url, args)

    @staticmethod
    def check_count_instances(
        django_testcase: django.test.TestCase, response: django.http.HttpResponse, args: dict
    ):
        # cls = apps.get_model("app", args["model"])
        # instances = list(cls.objects.all())
        instances = list(args["model"].objects.all())
        django_testcase.assertEqual(len(instances), args["n"])

    @staticmethod
    def check_dom_element(
        django_testcase: django.test.TestCase, response: django.http.HttpResponse, args: dict[manifest.DomArgument, Any]
    ):
        # NOTE: we do not support xpath as it is not supported by BeautifulSoup
        # this would require to use lxml
        # TODO: count number of elements from find_all

        soup = BeautifulSoup(response.content, "html.parser")

        # Apply the scope
        if scope := args.get(manifest.DomArgument.SCOPE):
            soup = soup.find(**scope)

        # Locate the element(s)
        # If find_all is provided, the checks are performed on ALL elements
        # If find is provided we enforce the result to be la list
        if args.get(manifest.DomArgument.FIND_ALL):
            dom_elements = soup.find_all(**args[manifest.DomArgument.FIND_ALL])
            django_testcase.assertGreaterEqual(len(dom_elements), 1)
        elif args.get(manifest.DomArgument.FIND):
            dom_element = soup.find(**args[manifest.DomArgument.FIND])
            django_testcase.assertIsNotNone(dom_element)
            dom_elements = [dom_element]
        else:
            raise ValueError("Neither find of find_all argument provided")

        # Perform the additional checks
        if count := args.get(manifest.DomArgument.COUNT):
            django_testcase.assertEqual(len(dom_elements), count)
        for dom_element in dom_elements:
            if text := args.get(manifest.DomArgument.TEXT):
                # TODO: this should/could disappear as text is too likely to change
                django_testcase.assertEqual(dom_element.text, text)
            if attribute := args.get(manifest.DomArgument.ATTRIBUTE):
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
