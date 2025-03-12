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

    @transaction.atomic
    def create(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item_ids = request.data.get("cart_item_ids", None)
        payment_method = request.data.get("payment_method", None)  # ✅ Get payment method

        if not payment_method:
            return Response({"error": "Payment method is required."}, status=status.HTTP_400_BAD_REQUEST)

        if payment_method not in dict(Order.PAYMENT_METHODS):
            return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)
        
        if cart_item_ids:
            items = CartItem.objects.filter(cart=cart, id__in=cart_item_ids)
        else:
            items = cart.items.all()
        
        if not items.exists():
            return Response({"error": "No valid items selected."}, status=status.HTTP_400_BAD_REQUEST)
        
        order = Order.objects.create(
            user=user, 
            total_price=0, 
            payment_method=payment_method,  # ✅ Save payment method
            payment_status="pending"  # ✅ Default payment status

        )
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

    def retrieve(self, request, pk=None):
        """Retrieve a single order by ID"""
        user = request.user
        try:
            order = Order.objects.get(id=pk, user=user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    

    @action(detail=True, methods=["POST"])
    def cancel(self, request, pk=None):
        """Allow customers to cancel their order if it is still 'Pending'."""
        user = request.user  # Get the logged-in user

        try:
            order = Order.objects.get(id=pk, user=user)  # Check if the order belongs to the user
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.status != "pending":  # Can only cancel if still Pending
            return Response({"error": "Order cannot be canceled."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = "canceled"  # Update status to "Canceled"
        order.save()
        return Response({"message": "Order canceled successfully."}, status=status.HTTP_200_OK)

class StoreOrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """List all orders for the store owned by the authenticated user."""
        if not hasattr(request.user, "store"):  # Check if user owns a store
            return Response({"error": "You do not own a store."}, status=status.HTTP_403_FORBIDDEN)

        store = request.user.store  # Get the store owned by the user
        orders = Order.objects.filter(items__book__store=store).distinct().order_by("-created_at")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class StoreOrderUpdateStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        """Allow store owners to update the status of their orders."""
        user = request.user  
        
        try:
            order = Order.objects.get(id=order_id, stores__owner=user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found or not authorized."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")

        # Updated allowed status transitions to match model
        allowed_transitions = {
            "pending": ["processing", "canceled"],
            "processing": ["shipped", "canceled"],
            "shipped": ["completed"],
            "completed": [],
            "canceled": [],
            "refunded": [],
        }

        if new_status not in allowed_transitions.get(order.status, []):
            return Response({"error": "Invalid status transition."}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()

        return Response({"message": f"Order status updated to {new_status}."}, status=status.HTTP_200_OK)