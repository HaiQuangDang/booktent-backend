from rest_framework import viewsets, permissions, generics, status
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.generics import ListAPIView
from django.db.models import Sum, Q
from books.models import Author, Genre, Book, GenreRequest
from books.serializers import AuthorSerializer, GenreSerializer, BookSerializer, AuthorBookSerializer, GenreBookSerializer, GenreRequestSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]  # <-- Allow anyone to access

    def perform_create(self, serializer):
        if (
            self.request.user.is_authenticated 
            and hasattr(self.request.user, "store") 
            and self.request.user.store.status == "active"
        ):
            serializer.save(store=self.request.user.store, status="pending")
        else:
            raise PermissionDenied("Only store owners with an active store can add books.")
        
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
    """Returns top 20 best-selling approved books; fills remaining with latest books"""
    serializer_class = BookSerializer
    permission_classes = []  # Public access

    def get_queryset(self):
        # Step 1: Top-selling approved books
        top_books = (
            Book.objects
            .filter(status="approved", store__status="active", orderitem__order__order_status="completed")
            .annotate(total_sold=Sum("orderitem__quantity"))
            .order_by("-total_sold")
            .distinct()
        )

        top_ids = list(top_books.values_list("id", flat=True)[:20])
        top_books_limited = top_books.filter(id__in=top_ids)

        # Step 2: Fill with latest approved books not in top_ids
        if len(top_ids) < 20:
            filler_books = (
                Book.objects
                .filter(status="approved", store__status="active")
                .exclude(id__in=top_ids)
                .order_by("-created_at")[:20 - len(top_ids)]
            )
            # Combine both QuerySets
            return list(top_books_limited) + list(filler_books)

        return top_books_limited


class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission to allow only admins to modify data."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # Allow read-only access to everyone
            return True
        return request.user and request.user.is_staff  # Only admins can modify

from rest_framework import filters

class AuthorViewSet(viewsets.ModelViewSet):  
    queryset = Author.objects.all().order_by("-created_at")
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']  # 👈 this enables ?search=name


class GenreViewSet(viewsets.ModelViewSet):  # Full CRUD
    queryset = Genre.objects.all().order_by("-created_at")
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]  # Read for all, modify for admins only

class AuthorBooksView(generics.RetrieveAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorBookSerializer
    lookup_field = 'id'  # URL will use `id`
    permission_classes = [permissions.AllowAny] 

class GenreBooksView(generics.RetrieveAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreBookSerializer
    lookup_field = 'id'  # URL will use `id`
    permission_classes = [permissions.AllowAny] 

class GenreRequestViewSet(viewsets.ModelViewSet):
    queryset = GenreRequest.objects.all()
    serializer_class = GenreRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(requested_by=self.request.user)

    def perform_create(self, serializer):
        if not hasattr(self.request.user, "store") or not self.request.user.store:
            raise permissions.PermissionDenied("Only store owners can request new genres.")
        if self.request.user.store.status != "active":
            raise permissions.PermissionDenied("You need an active store to request new genres.")
        serializer.save()

class BookSearchAPIView(ListAPIView):
    queryset = Book.objects.filter(status="approved")
    serializer_class = BookSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.query_params.get("q")

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(authors__name__icontains=query) |
                Q(genres__name__icontains=query)
            ).distinct()

        return queryset