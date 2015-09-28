Using Gabbi and Hypothesis to Test APIs
=======================================

In he world of testing it is important to write tests that are both easy to read and covering a wide range of scenarios. 
Often one of these will be sacrificed to facilitate the other, such as hard coding your examples so that your test 
logic remains clear or by creating an overly complicated setup so that multiple scenarios can be explored. Here we 
discuss two tools that when combined will allow you to explore more of the test surface of your web API while still 
creating clear and maintainable tests.

Hypothesis
==========

Hypothesis is a library that, when provided with a description of the parameters of your API will explore many 
situation that will stress your system allowing you to explore your API more thoroughly. When you have errors,
hypothesis will then work to simplify the failing example to show you the simplest failing case and then keep
this failing case in it's database to use until the problem is resolved.

Hypothesis uses, what it calls strategies to inject parameters into your test cases. These strategies produce random 
values from across the variable space including 'nasty' values such as min, max, nan and inf. In general this is done 
using a single decorator `given`, for example:

```python
from hypothesis import given
from hypothesis.strategies import floats

from my.module import add


@given(floats(), floats())
def test_float_addition_is_commutative(first, second):
    assert add(first, second) == add(second, first)
```

In general we want to test properties of our methods using hypothesis to avoid replicating the implementation in the 
test itself, this will help keep tests clear and independent of the implementation. For example we would probably not 
want to test:
 
```python
@given(floats(), floats())
def test_result_is_sum_of_first_and_second(first, second):
    assert add(first, second) == first + second
```

While it would be ok to write this test as it is sufficiently simple, for more complex examples such as encoding and 
decoding data you would likely not want to test the encoded result, instead you would test that given a value,
encoding and decoding gives the original result:
   
```python
@given(floats())
def test_encoding_and_decoding_a_value_gives_the_original_value(value):
    encoded = encode(value)
    assert decode(encoded) == value 
```

Testing like this gives us two major advantages:

1. The test is very clear and concise helping document the code
2. We are testing the behaviour we are actually interested in. Generally we are not interested in the encoded value, 
just that when we decode an encoded value we get the original value.
 
There are many good articles on property driven testing so we will not go into it any further here. The full 
documentation for hypothesis can be found [here](https://hypothesis.readthedocs.org/en/latest/index.html).

Gabbi
=====

Often when testing APIs we fall into the trap of testing that in a given situation the API call will be successful or 
error and let the test framework hide all the nasty details from us. While this is usually ok for your the javascript 
application, where we will either display the data on success or give some kind of error on failure, in the more 
general case http offers a lot of information to your API consumer, which we should make sure is present and correct 
if we want our APIs to be used by a wider audience.

It is also easy to hide away request construction in the test framework. By doing this it is difficult to know whether
we are actually testing the API in a way it will be used by the consumers or whether we are just hiding in some ideal
world. Remember, we need to be nasty to our applications in order to test them correctly. Of cource we can enforce all
of this in our testing framework but often this makes the test a lot harder to read.

Gabbi is a tool for declaratively creating tests for web APIs. It hopes to solve 2 problems:

1. Making aPI tests easier to read
2. Making testing of http requests more explicit

To do this gabbi uses yaml to declare the test API calls and the expected response. For example, lets take a look at a
simple web service which has a database of `Thing`s. To test the creation of a thing we may have something like:

```yaml
tests:
  - name: create thing
    url: /app/api/things/
    method: POST
    status: 201
    request_headers:
      content-type: application/json,
    data:
      name: my things name
        
  - name: fetch thing,
    url: /app/api/things/$RESPONSE["$.id"]/,
    response_json_paths:
      $.name: my things name
```

Here we are creating a `Thing`, making sure the request is a `POST`, the response code is 201 and that the correct 
content type is being sent. We also make sure that if we make a `GET` (default) request for the `Thing` created in the 
previous request by using `$RESPONSE`, we get a 200 status code (default) with json data that has the correct `name`.
These tests are very easy to read and can be very exhaustive.

Full gabbi documentation can be found [here](https://gabbi.readthedocs.org/en/latest/index.html).

Combining The Two
=================

The rest of this post will explore how these two tools can be used to create readable, parameterised tests for http API methods. The example is for a django project using django rest framework for the web API and can be found at 
https://github.com/wildfish/gabbi-hypothesis-demo.

If we want to parameterise our gabbi tests we can do by using environment variables using `$ENVIRON` this gives two
issues:

1. The actual tests cases (the yaml files) are separate from the code generating values.
2. The code generating the test values will be largely replicated code (lots of setting environment variable).

The first point is the major issue here. When your test code is split across multiple files it becomes difficult to 
maintain and it may also not be obvious what values are suitable for your test cases reducing faith in the test suite.
Here we hope to solve these by putting the gabbi declaration directly in the test case.

Custom Test Case
----------------

First thing we need to do is create a custom test case that will allow that will handle the hard work:

```python
import unittest

from django.test import LiveServerTestCase
from gabbi import case
from gabbi.driver import test_suite_from_yaml, RESPONSE_HANDLERS
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
            handler(case.HTTPTestCase)

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
```

First thing to note, our test case inherits from the django `TestCase` supplied by hypothesis as well as the 
`LiveServerTestCase` which will handle the database between hypothesis runs as well as creating the server to test 
against. Next we initialise the gabbi request handlers. Third we build the gabbi test suite from the declaration and
finally run the tests reporting any errors so that hypothesis can try and find a simpler error case.

Building Tests
--------------

If we go back to the example from above with a web app that stores `Thing`s we would start by writing:

```python
from hypothesis import given
from hypothesis.strategies import text
from .test_case import GabbiHypothesisTestCase

class ThingApi(GabbiHypothesisTestCase):
    @given(text())
    def test_object_is_created___object_has_correct_name_when_fetched(self, name):
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
                    '$.name': name
                }
            }],
        })
```

This is exactly the same test as above except we are taking the name for our object from hypothesis. When we run the
test we get the following output:

```
$ python manage.py test
Creating test database for alias 'default'...
Falsifying example: test_object_is_created___object_has_correct_name_when_fetched(self=<app.tests.ThingApi testMethod=test_object_is_created___object_has_correct_name_when_fetched>, name='')
F
======================================================================
FAIL: test_object_is_created___object_has_correct_name_when_fetched (app.tests.ThingApi)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/dan/workspace/wildfish/gabbihypothesisdemo/.hypothesis/eval_source/hypothesis_temporary_module_9669614f5505be38bfcae5a44a1d6cfa08e2c416.py", line 5, in test_object_is_created___object_has_correct_name_when_fetched
    return f(self, name)
  File "/home/dan/workspace/wildfish/pyenvs/gabbihypothesisdemo/lib/python3.4/site-packages/hypothesis/core.py", line 575, in wrapped_test
    print_example=True
  File "/home/dan/workspace/wildfish/pyenvs/gabbihypothesisdemo/lib/python3.4/site-packages/hypothesis/executors/executors.py", line 36, in execute
    return function()
  File "/home/dan/workspace/wildfish/pyenvs/gabbihypothesisdemo/lib/python3.4/site-packages/hypothesis/core.py", line 367, in run
    return test(*args, **kwargs)
  File "/home/dan/workspace/wildfish/gabbihypothesisdemo/app/tests.py", line 26, in test_object_is_created___object_has_correct_name_when_fetched
    '$.name': name
  File "/home/dan/workspace/wildfish/gabbihypothesisdemo/app/test_case.py", line 42, in run_gabi
    self.fail(s.getvalue())
AssertionError: FAIL: create thing
	'400' not found in ['201'], response:\r{\r  "name": [\r    "This field may not be blank."\r  ]\r}
FAIL: fetch thing
	unable to replace $RESPONSE in /app/api/things/$RESPONSE["$.id"]/, data unavailable: JSONPath '$.id' failed to match on data: '{'name': ['This field may not be blank.']}'
```

This gives us 2 pieces of information, firstly that it failed and secondly, that it failed because the API was passed
an empty string. This has shown us that our assumptions about what data can be handled by out API were false. Now we 
can add a new test case to cover the empty string example and refine our original test to ignore the value. It turns 
out that django rest framework will strip input of white space on cleaning the data so we will modify our tests to 
account for all 'empty' strings:  

```python
from hypothesis import given, assume
from hypothesis.strategies import text
from .test_case import GabbiHypothesisTestCase


class ThingApi(GabbiHypothesisTestCase):
    @given(text())
    def test_object_is_created___object_has_correct_name_when_fetched(self, name):
        assume(name.strip())

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
```

Here we introduce 2 new concepts from hypothesis, `filter` and `assume`. `filter` as you may expect, only gives values
that match the filter function. `assume` fails the test in a way that hypothesis will learn and start to favour giving
examples that match the assumption. When we run these tests we get:

```
$ python manage.py test
Creating test database for alias 'default'...
Falsifying example: test_object_is_created___object_has_correct_name_when_fetched(self=<app.tests.ThingApi testMethod=test_object_is_created___object_has_correct_name_when_fetched>, name='0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000')
F.
======================================================================
FAIL: test_object_is_created___object_has_correct_name_when_fetched (app.tests.ThingApi)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/dan/workspace/wildfish/gabbi-hypothesis-demo/.hypothesis/eval_source/hypothesis_temporary_module_9669614f5505be38bfcae5a44a1d6cfa08e2c416.py", line 5, in test_object_is_created___object_has_correct_name_when_fetched
    return f(self, name)
  File "/home/dan/workspace/wildfish/pyenvs/gabbi-hypothesis/lib/python3.4/site-packages/hypothesis/core.py", line 577, in wrapped_test
    print_example=True
  File "/home/dan/workspace/wildfish/pyenvs/gabbi-hypothesis/lib/python3.4/site-packages/hypothesis/executors/executors.py", line 36, in execute
    return function()
  File "/home/dan/workspace/wildfish/pyenvs/gabbi-hypothesis/lib/python3.4/site-packages/hypothesis/core.py", line 369, in run
    return test(*args, **kwargs)
  File "/home/dan/workspace/wildfish/gabbi-hypothesis-demo/app/tests.py", line 29, in test_object_is_created___object_has_correct_name_when_fetched
    '$.name': name.strip()
  File "/home/dan/workspace/wildfish/gabbi-hypothesis-demo/app/test_case.py", line 42, in run_gabi
    self.fail(s.getvalue())
AssertionError: FAIL: create thing
	'400' not found in ['201'], response:\r{\r  "name": [\r    "Ensure this field has no more than 255 characters."\r  ]\r}
FAIL: fetch thing
	unable to replace $RESPONSE in /app/api/things/$RESPONSE["$.id"]/, data unavailable: JSONPath '$.id' failed to match on data: '{'name': ['Ensure this field has no more than 255 characters.']}'
----------------------------------------------------------------------
Ran 2 tests in 0.016s

FAILED (failures=2)


----------------------------------------------------------------------
Ran 2 tests in 7.159s

FAILED (failures=1)
Destroying test database for alias 'default'...
```

So another assumption about our API was not correct. Our API cannot handle arbitrarily long names. Again we add a test
to cover this example and refine the original test:

```python
class ThingApi(GabbiHypothesisTestCase):
    @given(text())
    def test_object_is_created___object_has_correct_name_when_fetched(self, name):
        assume(name.strip() and len(name.strip()) < 255)

        self.run_gabi({
            ...
        })
    
    ...

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
```

When we run this we now all tests pass.

```
$ python manage.py test
Creating test database for alias 'default'...
...
----------------------------------------------------------------------
Ran 3 tests in 10.809s

OK
Destroying test database for alias 'default'...
```

A Note On Versioning
====================

Lets assume that this API was to be used by a wide audience and we wanted to change our model so that `name` was
actually stored as `first_name`, `middle_names` and `last_name`. We would be safe in making that change because our 
tests never use the model directly, the only thing we state in our tests is that using this version of the API our
consumers will be able to create an object by supplying the `name` parameter and when retrieving the object the `name`
parameter will be present with the correct value. If all tests pass we should be able to roll out our model change
safe in the knowledge our users using the old API will not have their applications immediately break. 

Conclusion
==========

We have seen how to combine hypothesis and gabbi to create tests for our API that are both readable and have high 
coverage by delegating the value selection. We have also seen how using these methods we can check and improve the 
assumptions we have made about our API. finally, property based tesing can be used to help keep testfaith for older
versions of you API.

Using these tests along with test driven development can ensure we get the API that we want to use and have great test
coverage.
