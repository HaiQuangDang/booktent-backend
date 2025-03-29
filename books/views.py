from rest_framework import viewsets, permissions, generics, status
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from books.models import Author, Genre, Book
from books.serializers import AuthorSerializer, GenreSerializer, BookSerializer, AuthorBookSerializer



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
        return Book.objects.filter(status='approved', store__status='active')

    def perform_create(self, serializer):
        """Only store owners with an active store can add books."""
        if (
            self.request.user.is_authenticated 
            and hasattr(self.request.user, "store") 
            and self.request.user.store.status == "active"
        ):
            serializer.save(store=self.request.user.store, status="pending")
        else:
            raise PermissionDenied("Only store owners with an active store can add books.")

        
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
    queryset = Book.objects.filter(status="approved", store__status="active")
    serializer_class = BookSerializer
    permission_classes = []  # Anyone can access



class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission to allow only admins to modify data."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # Allow read-only access to everyone
            return True
        return request.user and request.user.is_staff  # Only admins can modify

class AuthorViewSet(viewsets.ModelViewSet):  
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]  # Only admins can modify authors

class GenreViewSet(viewsets.ModelViewSet):  # Full CRUD
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]  # Read for all, modify for admins only

class AuthorBooksView(generics.RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorBookSerializer
    lookup_field = 'id'  # URL will use `id`
    permission_classes = [permissions.AllowAny] 

class GenreBooksView(generics.RetrieveAPIView):
    queryset = Genre.objects.all()
    serializer_class = AuthorBookSerializer
    lookup_field = 'id'  # URL will use `id`
    permission_classes = [permissions.AllowAny] 