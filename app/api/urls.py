from rest_framework.routers import DefaultRouter
from .thing import ThingViewSet

router = DefaultRouter()
router.register('thing', ThingViewSet)


urlpatterns = router.urls
