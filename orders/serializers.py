from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    book_title = serializers.ReadOnlyField(source="book.title")
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ["id", "book", "book_title", "quantity", "price", "total_price"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ["id", "user", "store", "items", "total_price", "payment_status", "created_at"]
