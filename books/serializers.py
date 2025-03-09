from rest_framework import serializers
from books.models import Author, Genre, Book
from stores.models import Store


class BookSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)  # Extra field
    # authors = serializers.StringRelatedField(many=True, read_only=True)
    # genres = serializers.StringRelatedField(many=True, read_only=True)

    authors = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Author.objects.all()
    )
    genres = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all()
    )
    author_names = serializers.SerializerMethodField()
    genre_names = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "description",
            "authors",
            "author_names", # This is NOT in the model, just for API response
            "genres",
            "genre_names",  # ✅ New field for genre names
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
    def get_author_names(self, obj):
        return [author.name for author in obj.authors.all()]

    def get_genre_names(self, obj):
        return [genre.name for genre in obj.genres.all()]
    # Update
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.status = "pending"  # Reset to pending after update
        instance.save()
        return instance


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'