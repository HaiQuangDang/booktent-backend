from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, AuthorViewSet, GenreViewSet, ApprovedBookListView
from .views import AuthorBooksView, GenreBooksView

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'book', BookViewSet, basename="book")  # Use explicit basename

urlpatterns = [
    path('', include(router.urls)),
    path('authors/<int:id>/books/', AuthorBooksView.as_view(), name='author-books'),
    path('genres/<int:id>/books/', GenreBooksView.as_view(), name='genre-books'),
    path('homepage/', ApprovedBookListView.as_view(), name='homepage-books'),  # Fixes manual view
]