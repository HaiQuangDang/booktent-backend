from rest_framework import serializers
from .models import Cart, CartItem
from books.models import Book

class CartItemSerializer(serializers.ModelSerializer):
    book_title = serializers.ReadOnlyField(source="book.title")
    store_id = serializers.ReadOnlyField(source="store.id")
    store_name = serializers.ReadOnlyField(source="store.name")
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ["id", "book", "book_title", "store_id", "store_name", "quantity", "price", "total_price"]

class CartSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_price"]

    def get_items(self, obj):
        sorted_items = obj.items.select_related('book', 'store').order_by('book__title')
        return CartItemSerializer(sorted_items, many=True).data

    def get_total_price(self, obj):
        return sum(item.total_price for item in obj.items.all())

