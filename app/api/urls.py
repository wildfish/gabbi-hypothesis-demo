from rest_framework.routers import DefaultRouter
from .thing import ThingViewSet

router = DefaultRouter()
router.register('things', ThingViewSet)


urlpatterns = router.urls
