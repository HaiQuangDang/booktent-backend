from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from books.models import Book
from .serializers import OrderSerializer
from stores.models import Store  # ✅ Import Store

class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item_ids = request.data.get("cart_item_ids", None)
        
        if cart_item_ids:
            items = CartItem.objects.filter(cart=cart, id__in=cart_item_ids)
        else:
            items = cart.items.all()
        
        if not items.exists():
            return Response({"error": "No valid items selected."}, status=status.HTTP_400_BAD_REQUEST)
        
        order = Order.objects.create(user=user, total_price=0)
        total_price = 0
        store_ids = set()  # ✅ Track unique store IDs
        
        for item in items:
            order_item = OrderItem.objects.create(
                order=order,
                book=item.book,
                quantity=item.quantity,
                price=item.price
            )
            total_price += item.total_price

            if item.book.store:  # ✅ Ensure book has a store
                store_ids.add(item.book.store.id)
        
            item.delete()  # Remove purchased items from cart
        
        order.total_price = total_price
        order.save()

        # ✅ Associate stores with the order
        print(f"📌 Store IDs found: {store_ids}")  # Debugging
        order.stores.set(store_ids)  # ✅ Assign stores to order
        order.save()
        
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        """List all orders for the authenticated user."""
        user = request.user
        orders = Order.objects.filter(user=user).order_by("-created_at")  # Show latest orders first
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
