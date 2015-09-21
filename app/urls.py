from django.conf.urls import include, url

urlpatterns = [
    url(r'^api/', include('app.api.urls', namespace='api')),
]
