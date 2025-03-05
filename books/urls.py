from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, AuthorViewSet, GenreViewSet, ApprovedBookListView

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'book', BookViewSet, basename="book")  # Use explicit basename

urlpatterns = [
    path('', include(router.urls)),  # Keeps all router-generated routes
    path('homepage/', ApprovedBookListView.as_view(), name='homepage-books'),  # Fixes manual view
]