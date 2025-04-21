from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, AuthorViewSet, GenreViewSet, ApprovedBookListView, RecentBookListView
from .views import AuthorBooksView, GenreBooksView, GenreRequestViewSet, BookSearchAPIView

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'book', BookViewSet, basename="book")
router.register(r'genres-request', GenreRequestViewSet, basename="genre-request")

urlpatterns = [
    path('', include(router.urls)),
    path('authors/<int:id>/books/', AuthorBooksView.as_view(), name='author-books'),
    path('genres/<int:id>/books/', GenreBooksView.as_view(), name='genre-books'),
    path('homepage/', ApprovedBookListView.as_view(), name='homepage-books'),
    path('recent/', RecentBookListView.as_view(), name='recent-books'),
    path("search/", BookSearchAPIView.as_view(), name="book-search"),
]