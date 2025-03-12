from rest_framework import serializers
from .models import Order, OrderItem
from stores.models import Store
from books.models import Book
import logging

logger = logging.getLogger(__name__)

class OrderItemSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    class Meta:
        model = OrderItem
        fields = "__all__"
        extra_fields = ["book_title"]  

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    stores = serializers.PrimaryKeyRelatedField(many=True, queryset=Store.objects.all(), required=False)
    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_METHODS, required=True)
    payment_status = serializers.ChoiceField(choices=Order.PAYMENT_STATUSES, read_only=True)


    class Meta:
        model = Order
        fields = "__all__"

    def create(self, validated_data):
        print("🔥🔥🔥 OrderSerializer.create() is running!")  # Debugging start point
        order = Order.objects.create(**validated_data)
        
        # Get store IDs from books in the order
        store_ids = set()
        for item in validated_data["items"]:
            print(f"🔍 Checking book {item.book.id} - Store: {item.book.store.id if item.book.store else 'No Store'}")  # Debugging print
            if item.book.store:  # Ensure book has a store
                store_ids.add(item.book.store.id)

        print(f"📌 Store IDs found: {store_ids}")  # Debugging print

        # Assign stores to order
        order.stores.set(store_ids)  # This should update the orders_order_stores table
        order.save()

        return order
