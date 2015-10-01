gabbi-hypothesis-demo
=====================

A small application to demonstrate how [hypothesis](https://hypothesis.readthedocs.org/en/latest/) can be used with 
[gabbi](https://gabbi.readthedocs.org/en/latest/index.html) to test REST apis.

See accompanying blog post at http://wildfish.com/blog/2015/10/01/using-gabbi-and-hypothesis-test-django-apis/.

We use [django](https://www.djangoproject.com/) and [django rest framework](http://www.django-rest-framework.org/) to 
create the service to test.

Setup
=====

After cloning this repo you will need to install its requirements using:
 
```
$> pip install -r requirements.txt
```

Then to test the service is set up correctly run:
 
```
$> python manage.py migrate
$> python manage.py runserver
```

This will start a web server on port 8000 which you can use to test the api by going to 
[http://localhost:8000/app/api/things].
