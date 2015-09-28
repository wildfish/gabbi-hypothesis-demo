from hypothesis import given, assume
from hypothesis.strategies import text
from .test_case import GabbiHypothesisTestCase


class ThingApi(GabbiHypothesisTestCase):
    @given(text())
    def test_object_is_created___object_has_correct_name_when_fetched(self, name):
        assume(name.strip() and len(name) < 255)

        self.run_gabi({
            'tests': [{
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
                    '$.name': name.strip()
                }
            }],
        })

    @given(text().filter(lambda x: not x.strip()))
    def test_object_name_is_blank___bad_request_status_is_given(self, name):
        self.run_gabi({
            'tests': [{
                'name': 'create thing',
                'url': '/app/api/things/',
                'method': 'POST',
                'status': 400,
                'request_headers': {
                    'content-type': 'application/json',
                },
                'data': {
                    'name': name
                },
                'response_json_paths': {
                    '$.name': ['This field may not be blank.']
                }
            }],
        })

    @given(text(min_size=256))
    def test_object_name_too_long___bad_request_status_is_given(self, name):
        assume(len(name.strip()) > 255)

        self.run_gabi({
            'tests': [{
                'name': 'create thing',
                'url': '/app/api/things/',
                'method': 'POST',
                'status': 400,
                'request_headers': {
                    'content-type': 'application/json',
                },
                'data': {
                    'name': name
                },
                'response_json_paths': {
                    '$.name': ['Ensure this field has no more than 255 characters.']
                }
            }],
        })
