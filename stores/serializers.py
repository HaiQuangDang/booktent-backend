from rest_framework import serializers
from .models import Store
from books.models import Book
from books.serializers import BookSerializer


class StoreSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")  # Show owner's username
    books = serializers.SerializerMethodField()  # Dynamically fetch books based on user

    class Meta:
        model = Store
        fields = ["id",
                  "name",
                  "description",
                  "owner",
                  "logo",
                  "created_at",
                  "updated_at",
                  "status",
                  "contact_info",
                  "books",
                  ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]  # Owner is set automatically

    def get_books(self, obj):
        """Retrieve books based on the user's role (owner sees all, others see approved)"""
        request = self.context.get("request")  # Get the current request
        if request and request.user == obj.owner:
            # If the logged-in user is the store owner, return all books
            books = Book.objects.filter(store=obj)
        else:
            # Otherwise, return only approved books
            books = Book.objects.filter(store=obj, status="approved")
        return BookSerializer(books, many=True, context={"request": request}).data  # Serialize books