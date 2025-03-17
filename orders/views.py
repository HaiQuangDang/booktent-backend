from rest_framework.decorators import action, api_view
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
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

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
        payment_method = request.data.get("payment_method", "cod").lower() # Default to COD

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
                    payment_method=payment_method,
                    payment_status = "pending" if payment_method == "online" else "unpaid"
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

class StripeCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        order_id = request.data.get("order_id")
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.payment_status == "PAID":
            return Response({"message": "Order already paid."}, status=status.HTTP_400_BAD_REQUEST)

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Order #{order.id}"
                        },
                        "unit_amount": int(order.total_price * 100),  # Convert to cents
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=settings.FRONTEND_URL + "/orders/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.FRONTEND_URL + f"/orders/{order.id}",
            metadata={"order_id": order.id}
        )

        return Response({"session_id": session.id, "url": session.url}, status=status.HTTP_200_OK)


@api_view(["POST"])
def payment_success(request):
    """Verify Stripe payment and update order status."""
    session_id = request.data.get("session_id")
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            order = Order.objects.filter(user=request.user, payment_status="pending").first()
            if order:
                order.payment_status = "paid"
                order.save()
            return Response({"message": "Payment verified!"})
    except stripe.error.StripeError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"error": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({"error": "Invalid signature"}, status=400)

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("Payment was successful!", session)
        # Update order payment status to "paid" here

    return JsonResponse({"status": "success"}, status=200)