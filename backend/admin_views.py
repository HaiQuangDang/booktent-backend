from django.contrib.auth.models import User
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils.timezone import now
from django.db.models.functions import TruncMonth
from django.db.models import Count
from datetime import timedelta


from stores.models import Store
from books.models import Book
from orders.models import Order
from transactions.models import Transaction

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


