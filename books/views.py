from rest_framework import viewsets, permissions
from django.core.exceptions import PermissionDenied
from books.models import Author, Genre, Book
from books.serializers import AuthorSerializer, GenreSerializer, BookSerializer

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]  # <-- Allow anyone to access

    def get_queryset(self):
        user = self.request.user

        # Admins see all books
        # if user.is_authenticated and user.is_staff:
        #     return Book.objects.all()

        # Store owners see all books from their store + approved books from others
        # if user.is_authenticated and hasattr(user, 'store'):
        #     return Book.objects.filter(store=user.store) | Book.objects.filter(status='approved')

        # Guests and normal users see only approved books
        return Book.objects.filter(status='approved')

    def perform_create(self, serializer):
        """Set book status to 'pending' when created by a store owner."""
        if self.request.user.is_authenticated and hasattr(self.request.user, 'store'):
            serializer.save(store=self.request.user.store, status='pending')
        else:
            raise PermissionDenied("Only store owners can add books.")


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):  # Read-Only
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]  # Anyone can view authors

class GenreViewSet(viewsets.ModelViewSet):  # Read-Only
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]  # Anyone can view genres