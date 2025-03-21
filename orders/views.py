from rest_framework.decorators import action, api_view
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from transactions.models import Transaction 
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
from django.shortcuts import get_object_or_404
from decimal import Decimal 

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer  

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
                    payment_status = "pending"
                )
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        book=item.book,
                        quantity=item.quantity,
                        price=item.price
                    )

                # **Create a Transaction for this order**
                admin_fee = total_price * Decimal("0.10")  # 10% fee
                store_earnings = total_price - admin_fee

                Transaction.objects.create(
                    order=order,
                    store=store,
                    amount=total_price,
                    admin_fee=admin_fee,
                    store_earnings=store_earnings,
                    payment_method=payment_method,
                    payment_status="pending"  # Will update after payment
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
    
    # Store
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_store_orders(self, request):
        """Return orders that contain books from the logged-in user's store."""
        user = request.user

        # Ensure the user has a store
        if not hasattr(user, "store"):
            return Response({"error": "You don't own a store."}, status=403)

        store = user.store  # Get the store owned by the user

        # Get orders that contain books from this store
        orders = Order.objects.filter(items__book__store=store).distinct()

        # Serialize and return the orders
        serializer = OrderSerializer(orders, many=True)  # Use OrderSerializer explicitly
        return Response(serializer.data)


class StripeCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_ids = request.data.get("order_ids", [])  # Expecting a list of order IDs

        if not order_ids:
            return Response({"error": "No orders provided"}, status=status.HTTP_400_BAD_REQUEST)

        orders = Order.objects.filter(id__in=order_ids, user=request.user, payment_status="pending")

        if not orders.exists():
            return Response({"error": "No valid unpaid orders found"}, status=status.HTTP_404_NOT_FOUND)

        total_price = sum(order.total_price for order in orders)

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Orders {', '.join(str(order.id) for order in orders)}"
                        },
                        "unit_amount": int(total_price * 100),  # Convert to cents
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=settings.FRONTEND_URL + "/orders/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.FRONTEND_URL + "/cart",
            metadata={"order_ids": ",".join(str(order.id) for order in orders)}
        )
        # Store the session ID in each order
        orders.update(stripe_session_id=session.id)

        return Response({"session_id": session.id, "url": session.url}, status=status.HTTP_200_OK)


# @api_view(["POST"])
# def payment_success(request):
#     """Verify Stripe payment and update order status."""
#     session_id = request.data.get("session_id")
#     print(session_id)
#     try:
#         session = stripe.checkout.Session.retrieve(session_id)
#         print(session)
#         if session.payment_status == "paid":
#             order = Order.objects.filter(user=request.user, payment_status="pending").first()
#             if order:
#                 order.payment_status = "paid"
#                 order.save()
#                 # ✅ Update the related transaction status to 'COMPLETED'
#                 transaction = Transaction.objects.filter(order=order, payment_status="pending").first()
#                 if transaction:
#                     transaction.payment_status = "paid"
#                     transaction.save()
#             return Response({"message": "Payment verified!"})
#     except stripe.error.StripeError as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#     return Response({"error": "Payment verification failed."}, status=status.HTTP_400_BAD_REQUEST)
@api_view(["POST"])
def payment_success(request):
    """Verify Stripe payment and update order & transaction status."""
    session_id = request.data.get("session_id")
    print(session_id)
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            # ✅ Find all orders linked to this session
            orders = Order.objects.filter(stripe_session_id=session_id)

            if not orders.exists():
                return Response({"error": "No matching pending orders found."}, status=status.HTTP_404_NOT_FOUND)

            # ✅ Update all orders & transactions
            with transaction.atomic():
                for order in orders:
                    order.payment_status = "paid"
                    order.save()

                    # ✅ Update transactions for this order
                    Transaction.objects.filter(order=order, payment_status="pending").update(payment_status="paid")

            return Response({"message": "Payment verified and orders updated!"})

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

class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    ALLOWED_TRANSITIONS = {
        "pending": ["processing"],
        "processing": ["shipped"],
        "shipped": ["completed", "refunded"],
        "completed": [],
        "canceled": [],
        "refunded": []
    }
    def patch(self, request, pk):  # ✅ Ensure we use 'pk' from the URL
        order = get_object_or_404(Order, id=pk, store__owner=request.user)  # ✅ Fix variable name
        new_status = request.data.get("order_status")

        # ✅ Check if status is valid
        if new_status not in dict(Order.ORDER_STATUS):
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check if transition is allowed
        if new_status not in self.ALLOWED_TRANSITIONS.get(order.order_status, []):  # ✅ Fix `order_status`
            return Response({"error": "Invalid status transition."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Update status
        order.order_status = new_status  # ✅ Fix `order_status`
        order.save()

        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
    
class StoreOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, store__owner=request.user)
        return Response(OrderSerializer(order).data)
    
class OrderCancellationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Allow customers or store owners to cancel an order."""
        order = get_object_or_404(Order, id=pk)

        # Check if the request is from the order's user OR the store owner
        if order.user != request.user and order.store.owner != request.user:
            return Response({"error": "You are not allowed to cancel this order."}, status=status.HTTP_403_FORBIDDEN)

        # Ensure the order can be canceled
        if order.order_status not in ["pending", "processing"]:
            return Response({"error": "Order cannot be canceled at this stage."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order.order_status = "canceled"

            # If the payment was online and already paid, mark it as refunded
            if order.payment_method == "online" and order.payment_status == "paid":
                order.payment_status = "refunded"
                Transaction.objects.filter(order=order, payment_status="paid").update(payment_status="refunded")

            order.save()

        return Response({"message": "Order canceled successfully."}, status=status.HTTP_200_OK)