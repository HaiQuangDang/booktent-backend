from django.shortcuts import render
# Create your views here.
from rest_framework import generics, permissions, serializers
from .models import Store
from .serializers import StoreSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from books.models import Book
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from decimal import Decimal
from orders.models import Order
from transactions.models import Transaction

class StoreListCreateView(generics.ListCreateAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        if Store.objects.filter(owner=self.request.user).exists():
            raise serializers.ValidationError({"detail": "You already have a store."})
        serializer.save(owner=self.request.user)  # Set the store owner to the logged-in user

class StoreDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_update(self, serializer):
        store = self.get_object()
        if self.request.user == store.owner or self.request.user.is_staff:
            serializer.save()
        else:
            raise permissions.PermissionDenied("You do not have permission to update this store.")

    def perform_destroy(self, instance):
        if self.request.user == instance.owner or self.request.user.is_staff:
            instance.delete()
        else:
            raise permissions.PermissionDenied("You do not have permission to delete this store.")

class MyStoreView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the store owned by the authenticated user"""
        try:
            store = Store.objects.get(owner=request.user)
            return Response(StoreSerializer(store).data)
        except Store.DoesNotExist:
            # return Response({"detail": "No store found"}, status=404)
            return Response({"detail": "No store found"})
        
# Store Dashboard
class StoreDashboardView(APIView):
    """Dashboard API for store owners to see an overview of their store"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ✅ Ensure the user is a store owner
        store = Store.objects.filter(owner=request.user).first()
        if not store:
            return Response({"error": "You do not own a store."}, status=403)

        # ✅ Total Orders
        total_orders = Order.objects.filter(store=store).count()

        # ✅ Total Earnings (only from completed orders)
        total_earnings = Transaction.objects.filter(
            store=store, status="completed"
        ).aggregate(total=Sum("store_earnings"))["total"] or Decimal("0.00")

        # ✅ Low Stock Books (stock < 5)
        low_stock_books = list(
            store.books.filter(stock_quantity__lt=5).values("title", "stock_quantity")
        )

        # ✅ Recent Orders (last 5)
        recent_orders = list(
            Order.objects.filter(store=store)
            .order_by("-created_at")[:5]
            .values("id", "total_price", "order_status", "created_at")
        )

        # ✅ Recent Books (last 5 added)
        recent_books = list(
            store.books.order_by("-created_at")[:5].values("id", "title", "price", "stock_quantity")
        )

        # ✅ Recent Transactions (last 5)
        recent_transactions = list(
            Transaction.objects.filter(store=store, status="completed")
            .order_by("-created_at")[:5]
            .values("id", "amount", "status", "created_at")
        )

        # ✅ Return all data in one response
        return Response({
            "total_orders": total_orders,
            "total_earnings": total_earnings,
            "low_stock_books": low_stock_books,
            "recent_orders": recent_orders,
            "recent_books": recent_books,
            "recent_transactions": recent_transactions
        })