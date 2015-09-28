import unittest

from django.test import LiveServerTestCase
from gabbi.driver import test_suite_from_yaml, RESPONSE_HANDLERS
from gabbi.case import HTTPTestCase
from gabbi.reporter import ConciseTestRunner
from hypothesis.extra.django import TestCase
from six import StringIO


class GabbiHypothesisTestCase(TestCase, LiveServerTestCase):
    def run_gabi(self, gabbi_declaration):
        for handler in RESPONSE_HANDLERS:
            handler(HTTPTestCase)

        _, host = self.live_server_url.split('://')

        suite = test_suite_from_yaml(
            unittest.defaultTestLoader,
            self.id(),
            gabbi_declaration,
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
