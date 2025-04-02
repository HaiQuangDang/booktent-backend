from rest_framework import serializers
from .models import Store
from books.models import Book
from books.serializers import BookSerializer

class StoreSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")  
    books = serializers.SerializerMethodField()  

    class Meta:
        model = Store
        fields = [
            "id", "name", "description", "owner", "logo",
            "created_at", "updated_at", "status", "contact_info", "books"
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def get_books(self, obj):
        """Retrieve books based on the user's role (owner sees all, others see approved)"""
        try:
            request = self.context.get("request")
            books = obj.books.all()  # Get all books for this store

            if request and request.user != obj.owner:
                # Non-owner users see only approved books
                books = books.filter(status="approved")

            # ✅ Pass `{"request": request}` like in AuthorBookSerializer
            return BookSerializer(books, many=True, context={"request": request}).data
        except Exception as e:
            return {"error": f"Error retrieving books: {str(e)}"}
