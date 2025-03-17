from rest_framework.decorators import action 
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from books.models import Book
from .serializers import OrderSerializer
from stores.models import Store
from rest_framework.views import APIView

class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        """Place an order from selected cart items."""
        user = request.user
        cart = Cart.objects.filter(user=user).first()

        if not cart or not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        selected_item_ids = request.data.get("cart_item_ids", [])  # List of selected cart item IDs
        if not selected_item_ids:
            return Response({"error": "No items selected"}, status=status.HTTP_400_BAD_REQUEST)

        payment_method = request.data.get("payment_method", "COD")  # Default to COD

        orders = []  # To store created orders
        store_orders = {}  # Group selected cart items by store

        # Filter only selected items
        selected_items = cart.items.filter(id__in=selected_item_ids)
        
        if not selected_items.exists():
            return Response({"error": "No valid items found"}, status=status.HTTP_400_BAD_REQUEST)

        # Group selected items by store
        for item in selected_items:
            store_orders.setdefault(item.book.store, []).append(item)

        with transaction.atomic():  # Ensure atomicity
            for store, items in store_orders.items():
                total_price = sum(item.total_price for item in items)
                order = Order.objects.create(
                    user=user,
                    store=store,
                    total_price=total_price,
                    payment_status="pending" if payment_method == "online" else "cod"
                )
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        book=item.book,
                        quantity=item.quantity,
                        price=item.price
                    )
                orders.append(order)

            # Remove only the ordered items from the cart
            selected_items.delete()

        return Response(OrderSerializer(orders, many=True).data, status=status.HTTP_201_CREATED)


    def list(self, request):
        """Get all user orders."""
        user = request.user
        orders = Order.objects.filter(user=user)
        return Response(OrderSerializer(orders, many=True).data)

    def retrieve(self, request, pk=None):
        """Get a single order's details."""
        user = request.user
        try:
            order = Order.objects.get(id=pk, user=user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(OrderSerializer(order).data)

    def confirm_payment(self, request, pk=None):
        """Confirm payment for an order.
            1️⃣ User pays via online method (handled on the frontend).
            2️⃣ Frontend sends a request to confirm payment, calling this API.
            3️⃣ Backend checks:
                Does the order exist? ❌ → Return 404 Not Found.
                Is it already paid? ✅ → Return "Payment already confirmed".
                Is it an online payment order? ❌ → Return "Cannot confirm payment for this method".
            4️⃣ If all checks pass, backend updates payment_status = "PAID".
            5️⃣ Success response: {"message": "Payment confirmed successfully."}.
            👉 For Cash on Delivery (COD): No need to confirm, since the payment happens on delivery.

            This flow ensures only online payments get confirmed, preventing fraud or double confirmations.
        """
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.payment_status == "PAID":
            return Response({"message": "Payment already confirmed."}, status=status.HTTP_200_OK)

        if order.payment_method != "ONLINE":
            return Response({"error": "Cannot confirm payment for this method."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark the order as paid
        order.payment_status = "PAID"
        order.save()

        return Response({"message": "Payment confirmed successfully."}, status=status.HTTP_200_OK)
