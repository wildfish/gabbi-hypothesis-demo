import unittest

from django.test import LiveServerTestCase
from gabbi.driver import test_suite_from_yaml, RESPONSE_HANDLERS
from gabbi.case import HTTPTestCase
from gabbi.reporter import ConciseTestRunner
from hypothesis import given, assume
from hypothesis.extra.django import TestCase
from hypothesis.strategies import text
from six import StringIO


class GabbiHypothesisTestCase(TestCase, LiveServerTestCase):
    def run_gabi(self, base_test_name, tests):
        for handler in RESPONSE_HANDLERS:
            handler(HTTPTestCase)

        _, host = self.live_server_url.split('://')

        suite = test_suite_from_yaml(
            unittest.defaultTestLoader,
            base_test_name,
            {'tests': tests},
            '.',
            host,
            None,
            None,
            None,
        )

        s = StringIO()
        result = ConciseTestRunner(stream=s, verbosity=0).run(suite)

        if not result.wasSuccessful():
            self.fail(s.getvalue())


class ThingApi(GabbiHypothesisTestCase):
    @given(text())
    def test_object_is_created___object_has_correct_name_when_fetched(self, name):
        assume(name)
        self.run_gabi(
            'test_object_is_created___object_has_correct_name_when_fetched',
            [
                {
                    'name': 'create thing',
                    'url': '/app/api/things/',
                    'method': 'POST',
                    'status': 201,
                    'request_headers': {
                        'content-type': 'application/json',
                    },
                    'data': {
                        'name': name
                    }
                },
                {
                    'name': 'fetch thing',
                    'url': '/app/api/things/$RESPONSE["$.id"]/',
                    'response_json_paths': {
                        '$.name': name
                    }
                },
            ]
        )

    def test_object_name_is_blank___bad_request_status_is_given(self):
        self.run_gabi(
            'test_object_is_created___object_has_correct_name_when_fetched',
            [
                {
                    'name': 'create thing',
                    'url': '/app/api/things/',
                    'method': 'POST',
                    'status': 400,
                    'request_headers': {
                        'content-type': 'application/json',
                    },
                    'data': {
                        'name': ''
                    },
                    'response_json_paths': {
                        '$.name': ['This field may not be blank.']
                    }
                },
            ]
        )