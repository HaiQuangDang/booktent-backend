from rest_framework import viewsets, permissions, generics, status
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response
from books.models import Author, Genre, Book
from books.serializers import AuthorSerializer, GenreSerializer, BookSerializer



class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]  # <-- Allow anyone to access

    def get_queryset(self):
        user = self.request.user

        # Admins see all books
        if user.is_authenticated and user.is_staff:
            return Book.objects.all()

        # Store owners see all books from their store + approved books from others
        if user.is_authenticated and hasattr(user, 'store'):
            return Book.objects.filter(store=user.store) | Book.objects.filter(status='approved')

        # Guests and normal users see only approved books
        return Book.objects.filter(status='approved')

    def perform_create(self, serializer):
        """Set book status to 'pending' when created by a store owner."""
        if self.request.user.is_authenticated and hasattr(self.request.user, 'store'):
            serializer.save(store=self.request.user.store, status='pending')
        else:
            raise PermissionDenied("Only store owners can add books.")
    # Update

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Set status to pending after updating
        book = self.get_object()
        book.status = "pending"
        book.save()
        return response
    def destroy(self, request, *args, **kwargs):
        book = self.get_object()

        # Check if the request user owns the store that owns this book
        if book.store.owner != request.user:
            raise PermissionDenied("You can only delete books from your own store.")

        # Proceed with deletion
        self.perform_destroy(book)
        return Response({"detail": "Book deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class ApprovedBookListView(generics.ListAPIView):
    """Returns only approved books for the homepage"""
    queryset = Book.objects.filter(status="approved")
    serializer_class = BookSerializer
    permission_classes = []  # Anyone can access


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):  # Read-Only
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [permissions.AllowAny]  # Anyone can view authors

class GenreViewSet(viewsets.ModelViewSet):  # Read-Only
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]  # Anyone can view genres