import unittest

from django.test import LiveServerTestCase
from gabbi.driver import test_suite_from_yaml, RESPONSE_HANDLERS
from gabbi.case import HTTPTestCase
from gabbi.reporter import ConciseTestRunner
from hypothesis.extra.django import TestCase
from six import StringIO


class GabbiHypothesisTestCase(TestCase, LiveServerTestCase):
    """
    Test case to handle running gabbi tests along with hypothesis in django applications.
    """
    def run_gabi(self, gabbi_declaration):
        # initialise the gabbi handlers
        for handler in RESPONSE_HANDLERS:
            handler(HTTPTestCase)

        # take only the host name and port from the live server
        _, host = self.live_server_url.split('://')

        # use gabbi to create the test suite from our declaration
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

        # run the test (we store the the output into a custom stream so that hypothesis can display only the simple
        # case test result on failure rather than every failing case)
        s = StringIO()
        result = ConciseTestRunner(stream=s, verbosity=0).run(suite)

        # if we weren't successfull we need to fail the test case with the error string from gabbi
        if not result.wasSuccessful():
            self.fail(s.getvalue())
