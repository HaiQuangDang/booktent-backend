from django.contrib.auth.models import User
from django.db.models import Sum
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django.db.utils import IntegrityError

from books.serializers import BookSerializer, GenreRequestSerializer
from orders.serializers import OrderSerializer
from transactions.serializers import SiteConfigSerializer

from stores.models import Store
from books.models import Book, GenreRequest, Genre
from orders.models import Order
from transactions.models import Transaction, SiteConfig

@api_view(["GET"])
@permission_classes([IsAdminUser])  # Only admins can access
def admin_stats(request):
    stats = {
        "total_users": User.objects.count(),
        "total_stores": Store.objects.filter(status="active").count(),
        "pending_stores": Store.objects.filter(status="pending").count(),
        "total_books": Book.objects.filter(status="approved").count(),
        "pending_books": Book.objects.filter(status="pending").count(),
        "total_orders": Order.objects.count(),
        "total_earnings": Transaction.objects.aggregate(Sum("admin_fee"))["admin_fee__sum"] or 0,
    }
    return Response(stats)

@api_view(["GET"])
@permission_classes([IsAdminUser])  # Only admins can access
def recent_activity(request):
    activity = {
        "pending_stores": list(Store.objects.filter(status="pending").order_by("-created_at")[:5].values("id", "name", "owner__username", "created_at")),
        "pending_books": list(Book.objects.filter(status="pending").order_by("-created_at")[:5].values("id", "title", "store__name", "created_at")),
        "recent_orders": list(Order.objects.order_by("-created_at")[:5].values("id", "user__username", "total_price", "order_status", "created_at")),
        "recent_transactions": list(Transaction.objects.order_by("-created_at")[:5].values("id", "order__id", "amount", "admin_fee", "created_at")),
    }
    return Response(activity)

from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.db.models import Count

@api_view(["GET"])
@permission_classes([IsAdminUser])  # Only admins can access
def earnings_stats(request):
    today = now().date()
    first_day_this_month = today.replace(day=1)
    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)

    # Earnings for this month
    total_earnings_this_month = Transaction.objects.filter(created_at__gte=first_day_this_month).aggregate(Sum("admin_fee"))["admin_fee__sum"] or 0

    # Earnings for last month
    total_earnings_last_month = Transaction.objects.filter(created_at__gte=first_day_last_month, created_at__lt=first_day_this_month).aggregate(Sum("admin_fee"))["admin_fee__sum"] or 0

    # Earnings per month (last 6 months)
    earnings_per_month = (
        Transaction.objects
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total_earnings=Sum("admin_fee"))
        .order_by("-month")[:6]
    )

    data = {
        "total_earnings_this_month": total_earnings_this_month,
        "total_earnings_last_month": total_earnings_last_month,
        "earnings_per_month": list(earnings_per_month),
    }
    return Response(data)

class AdminBookListView(generics.ListAPIView):
    queryset = Book.objects.all().order_by("-created_at")
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admin can access

class AdminDeleteBookView(generics.DestroyAPIView):
    queryset = Book.objects.all()
    permission_classes = [permissions.IsAdminUser]  

class AdminUpdateBookStatusView(generics.UpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admin can update

    def update(self, request, *args, **kwargs):
        book = self.get_object()
        new_status = request.data.get("status")

        if new_status not in ["pending", "approved", "rejected"]:
            return Response({"error": "Invalid status."}, status=400)

        book.status = new_status
        book.save()
        return Response({"message": f"Book status updated to {new_status}"})


class AdminOrderListView(generics.ListAPIView):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can access

class AdminOrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can access

    def get_object(self):
        order_id = self.kwargs["pk"]
        return get_object_or_404(Order, id=order_id)
    

@api_view(["GET", "PATCH"])
@permission_classes([IsAdminUser])
def admin_fee_view(request):
    """Get or update the admin fee percentage"""
    config = SiteConfig.objects.first()

    if request.method == "PATCH":
        serializer = SiteConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    serializer = SiteConfigSerializer(config)
    return Response(serializer.data)

class GenreRequestAdminViewSet(viewsets.ModelViewSet):
    queryset = GenreRequest.objects.all()
    serializer_class = GenreRequestSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        genre_request = self.get_object()
        if genre_request.status != "pending":
            return Response({"error": "Already processed"}, status=400)
        
        try:
            # Create the Genre
            Genre.objects.create(
                name=genre_request.name,
                description=genre_request.description or ""
            )
            # Update the request
            genre_request.status = "approved"
            genre_request.reviewed_at = now()
            genre_request.save()
            return Response({"status": "approved"})
        except IntegrityError:  # This was catching the wrong one
            return Response({"error": "Genre name already exists"}, status=400)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=500)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        genre_request = self.get_object()
        if genre_request.status != "pending":
            return Response({"error": "Already processed"}, status=400)
        genre_request.status = "rejected"
        genre_request.reviewed_at = now()
        genre_request.save()
        return Response({"status": "rejected"})