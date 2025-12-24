from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiscoverViewSet, SwipeViewSet, MatchViewSet

router = DefaultRouter()
router.register(r'discover', DiscoverViewSet, basename='discover')
router.register(r'swipes', SwipeViewSet, basename='swipe')
router.register(r'matches', MatchViewSet, basename='match')

urlpatterns = [
    path('', include(router.urls)),
]