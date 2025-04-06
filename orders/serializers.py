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
    customer_name = serializers.CharField(source="user.username", read_only=True)  # Get customer's name
    store_name = serializers.CharField(source="store.name", read_only=True)  # Get store's name

    class Meta:
        model = Order
        fields = [
            "id", "user", "customer_name", "address", "phone", "order_status", "store", "store_name",
            "items", "total_price", "payment_method", "payment_status", "created_at"
        ]