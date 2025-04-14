from rest_framework import serializers
from books.models import Author, Genre, Book, GenreRequest
from stores.models import Store
class BookSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)
    
    authors = serializers.ListField(child=serializers.CharField(), write_only=True)

    # Include the full author objects (with IDs) for reading
    author_details = serializers.SerializerMethodField()
    # Genres as IDs
    genres = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all()
    )
    genre_names = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "description",
            "authors",           # Write-only for name input
            "author_details",    # Read-only with IDs and names
            "genres",
            "genre_names",
            "store",
            "store_name",
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
        request = self.context["request"]
        if request.user.is_staff:
            return value  # Admins can update any store
        if not Store.objects.filter(id=value.id, owner=request.user).exists():
            raise serializers.ValidationError("You can only add books to your own store.")
        return value

    def get_author_details(self, obj):
        return [{"id": author.id, "name": author.name} for author in obj.authors.all()]

    def get_genre_names(self, obj):
        return [genre.name for genre in obj.genres.all()]


    def create(self, validated_data):
        try:
            author_names = validated_data.pop('authors', [])
            genres = validated_data.pop("genres")
            book = Book.objects.create(**validated_data)

            for name in author_names:
                author, _ = Author.objects.get_or_create(name=name.strip())
                book.authors.add(author)
            book.genres.set(genres)
            return book
        except Exception as e: 
            raise serializers.ValidationError(f"Error creating book: {str(e)}")




    def update(self, instance, validated_data):
        try:
            if "authors" in validated_data:
                authors = validated_data.pop("authors")
                instance.authors.set(authors)
            if "genres" in validated_data:
                genres = validated_data.pop("genres")
                instance.genres.set(genres)
            instance = super().update(instance, validated_data)
            instance.status = "pending"
            instance.save()
            return instance
        except Exception as e:      
            raise serializers.ValidationError(f"Error updating book: {str(e)}")

class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = '__all__'
        
class AuthorBookSerializer(serializers.ModelSerializer):
    books = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['id', 'name', 'books']

    def get_books(self, obj):
        try:
            request = self.context.get("request")
            approved_books = obj.books.filter(status="approved")
            if not approved_books.exists():
                return []
            return BookSerializer(
                approved_books,
                many=True,
                context={"request": request}
            ).data
        except Exception as e:
            return {"error": f"Error retrieving books: {str(e)}"}

class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = '__all__'

class GenreBookSerializer(serializers.ModelSerializer):
    books = serializers.SerializerMethodField()

    class Meta:
        model = Genre
        fields = ['id', 'name', 'books']

    def get_books(self, obj):
        try:
            # Get request from context
            request = self.context.get("request")
            
            # Filter approved books
            approved_books = obj.books.filter(status="approved")
            
            # Check if books exist
            if not approved_books.exists():
                return []
                
            # Serialize the books with proper context
            return BookSerializer(
                approved_books,
                many=True,
                context={"request": request}
            ).data
        except Exception as e:
            # Handle any unexpected errors
            return {"error": f"Error retrieving books: {str(e)}"}
        
class GenreRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenreRequest
        fields = ["id", "name", "description", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def create(self, validated_data):
        # Automatically set the requesting user
        validated_data["requested_by"] = self.context["request"].user
        return super().create(validated_data)