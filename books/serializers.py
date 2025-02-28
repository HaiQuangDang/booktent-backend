from rest_framework import serializers
from .models import Book
from stores.models import Store

class BookSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)  # Extra field
    authors = serializers.StringRelatedField(many=True, read_only=True)
    genres = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "description",
            "authors",
            "genres",
            "store",
            "store_name",  # This is NOT in the model, just for API response
            "price",
            "stock_quantity",
            "published_year",
            "cover_image",
            "created_at",
            "updated_at",
            "status",
        ]
        read_only_fields = ["id", "store_name", "created_at", "updated_at", "status"]

    def validate_store(self, value):
        """Ensure that the user can only add books to their own store"""
        request = self.context["request"]
        if not Store.objects.filter(id=value.id, owner=request.user).exists():
            raise serializers.ValidationError("You can only add books to your own store.")
        return value
