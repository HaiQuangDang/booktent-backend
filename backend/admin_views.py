from django.contrib.auth.models import User
from rest_framework.views import APIView
from django.db.models import Sum, F
from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils.timezone import now
from django.utils import timezone
from django.db.models.functions import TruncMonth, TruncDate, TruncYear, TruncDay, TruncWeek
from datetime import timedelta, datetime
from django.shortcuts import get_object_or_404
from django.db.utils import IntegrityError
from django.db.models import Count
from books.serializers import BookSerializer, GenreRequestSerializer
from orders.serializers import OrderSerializer
from transactions.serializers import SiteConfigSerializer
from rest_framework.pagination import PageNumberPagination

from stores.models import Store
from books.models import Book, GenreRequest, Genre, Author
from orders.models import Order, OrderItem
from transactions.models import Transaction, SiteConfig

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

 
@api_view(["GET"])
@permission_classes([IsAdminUser])  # Only admins can access
def admin_stats(request):
    today = now().date()

    # Get all orders from today
    today_orders = Order.objects.filter(created_at__date=today)

    # Total orders today
    total_orders_today = today_orders.count()

    # Total books sold today (sum of quantities in today's order items)
    total_books_sold_today = OrderItem.objects.filter(order__created_at__date=today).aggregate(
        total=Sum("quantity")
    )["total"] or 0

    # Total admin earnings from completed transactions today
    earnings_today = Transaction.objects.filter(
        created_at__date=today,
        status="completed"
    ).aggregate(total=Sum("admin_fee"))["total"] or 0

    return Response({
        "orders_today": total_orders_today,
        "books_sold_today": total_books_sold_today,
        "earnings_today": round(earnings_today, 2),
    })

@api_view(["GET"])
@permission_classes([IsAdminUser]) 
def recent_activity(request):
    activity = {
        "pending_stores": list(Store.objects.filter(status="pending").order_by("-created_at")[:5].values("id", "name", "owner__username", "created_at")),
        "pending_books": list(Book.objects.filter(status="pending").order_by("-created_at")[:5].values("id", "title", "store__name", "created_at")),
        "recent_orders": list(Order.objects.order_by("-created_at")[:5].values("id", "user__username", "total_price", "order_status", "created_at")),
        "recent_transactions": list(Transaction.objects.order_by("-created_at")[:5].values("id", "order__id", "amount", "admin_fee", "created_at")),
    }
    return Response(activity)

@api_view(["GET"])
@permission_classes([IsAdminUser])
def earnings_stats(request):
    today = timezone.now()

    # Define the start of the week, month, and year
    start_of_week = today - timedelta(days=today.weekday())  # Monday of the current week
    start_of_month = today.replace(day=1)  # First day of the current month
    start_of_year = today.replace(month=1, day=1)  # First day of the current year

    # Total earnings for this week, this month, and this year
    total_earnings_this_week = Transaction.objects.filter(
        created_at__gte=start_of_week
    ).aggregate(Sum("admin_fee"))["admin_fee__sum"] or 0

    total_earnings_this_month = Transaction.objects.filter(
        created_at__gte=start_of_month
    ).aggregate(Sum("admin_fee"))["admin_fee__sum"] or 0

    total_earnings_this_year = Transaction.objects.filter(
        created_at__gte=start_of_year
    ).aggregate(Sum("admin_fee"))["admin_fee__sum"] or 0

    # Earnings breakdown for the week, month, and year
    earnings_weekly = (
        Transaction.objects
        .annotate(week=TruncDate(TruncWeek("created_at")))
        .values("week")
        .annotate(earnings=Sum("admin_fee"))
        .filter(week__gte=start_of_year)  # Ensure we don't get future weeks
        .order_by("-week")
    )

    earnings_monthly = (
        Transaction.objects
        .annotate(month=TruncDate(TruncMonth("created_at")))
        .values("month")
        .annotate(earnings=Sum("admin_fee"))
        .filter(month__gte=start_of_year)  # Ensure we don't get future months
        .order_by("-month")
    )

    earnings_yearly = (
        Transaction.objects
        .annotate(year=TruncDate(TruncYear("created_at")))
        .values("year")
        .annotate(earnings=Sum("admin_fee"))
        .order_by("-year")
    )

    # Prepare the data to be returned
    data = {
        "total_earnings_this_week": total_earnings_this_week,
        "total_earnings_this_month": total_earnings_this_month,
        "total_earnings_this_year": total_earnings_this_year,
        "earnings_weekly": list(earnings_weekly),
        "earnings_monthly": list(earnings_monthly),
        "earnings_yearly": list(earnings_yearly),
    }

    return Response(data)

# View to get recently added authors (added in the last 7 days)
@api_view(["GET"])
@permission_classes([IsAdminUser])  # Only admins can access
def recent_authors(request):
    seven_days_ago = timezone.now() - timedelta(days=7)
    authors = Author.objects.filter(created_at__gte=seven_days_ago).order_by("-created_at")
    author_data = authors.values("id", "name", "created_at")
    return Response({"recent_authors": list(author_data)})


# View to get requested genres with their status
@api_view(["GET"])
@permission_classes([IsAdminUser])  # Only admins can access
def genre_requests(request):
    genre_requests = GenreRequest.objects.all().order_by("-created_at")
    genre_request_data = genre_requests.values("id", "name", "status", "requested_by__username", "created_at")
    return Response({"genre_requests": list(genre_request_data)})

@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_book_stats(request):
    today = now().date()
    current_year = today.year
    current_month = today.month

    # Top 10 best-selling books
    top_selling_books = (
        OrderItem.objects
        .values("book__id", "book__title")
        .annotate(sold=Sum("quantity"))
        .order_by("-sold")[:10]
    )

    # All order items
    all_items = OrderItem.objects.all()

    # Basic sales totals
    daily_sales = all_items.filter(order__created_at__date=today).aggregate(
        total=Sum("quantity")
    )["total"] or 0

    monthly_sales = all_items.filter(
        order__created_at__year=current_year,
        order__created_at__month=current_month,
    ).aggregate(total=Sum("quantity"))["total"] or 0

    yearly_sales = all_items.filter(
        order__created_at__year=current_year
    ).aggregate(total=Sum("quantity"))["total"] or 0

    # Per-day sales for last 7 days
    last_week = today - timedelta(days=6)
    daily_breakdown = (
        all_items.filter(order__created_at__date__gte=last_week)
        .annotate(day=TruncDate("order__created_at"))
        .values("day")
        .annotate(quantity=Sum("quantity"))
        .order_by("day")
    )

    # Per-month sales for current year
    monthly_breakdown = (
        all_items.filter(order__created_at__year=current_year)
        .annotate(month=TruncDate(TruncMonth("order__created_at")))
        .values("month")
        .annotate(quantity=Sum("quantity"))
        .order_by("month")
    )

    # Per-year sales for past years
    yearly_breakdown = (
        all_items
        .annotate(year=TruncDate(TruncYear("order__created_at")))
        .values("year")
        .annotate(quantity=Sum("quantity"))
        .order_by("year")
    )

    return Response({
        "top_selling_books": list(top_selling_books),
        "sales_stats": {
            "daily_sales": daily_sales,
            "monthly_sales": monthly_sales,
            "yearly_sales": yearly_sales,
            "daily_breakdown": list(daily_breakdown),
            "monthly_breakdown": list(monthly_breakdown),
            "yearly_breakdown": list(yearly_breakdown),
        }
    })


class AdminBookListView(generics.ListAPIView):
    queryset = Book.objects.all().order_by("-created_at")
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination  # Apply custom pagination

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by status if the status is provided in the request
        status = self.request.query_params.get("status", None)
        if status in ["pending", "approved", "rejected"]:
            queryset = queryset.filter(status=status)

        return queryset

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
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Order.objects.all().order_by("-created_at")

        # Manual filters
        order_status = self.request.query_params.get("order_status")
        payment_method = self.request.query_params.get("payment_method")

        if order_status:
            queryset = queryset.filter(order_status=order_status)

        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        return queryset

class AdminOrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can access

    def get_object(self):
        order_id = self.kwargs["pk"]
        return get_object_or_404(Order, id=order_id)
    

@api_view(["GET", "PATCH"])
def admin_fee_view(request):
    config = SiteConfig.objects.first()

    if request.method == "PATCH":
        if not request.user.is_staff:
            return Response({"detail": "You do not have permission to perform this action."}, status=403)
        serializer = SiteConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    if not request.user.is_authenticated:
        return Response({"detail": "Authentication credentials were not provided."}, status=401)

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
    
class AdminStoreOrderDashboardView(APIView):
    permission_classes = [IsAdminUser]  # Only allow admin users

    def get(self, request):
        store_id = request.query_params.get("store_id")
        if not store_id:
            return Response({"error": "Missing store_id in query parameters."}, status=400)

        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response({"error": "Store not found."}, status=404)

        orders = Order.objects.filter(store=store)

        query_date_str = request.query_params.get("date")
        query_date_orders = None
        if query_date_str:
            try:
                query_date = datetime.strptime(query_date_str, "%Y-%m-%d").date()
                query_date_orders = orders.filter(created_at__date=query_date).count()
            except ValueError:
                query_date_orders = "Invalid date format. Use YYYY-MM-DD."

        # Time setup
        today = now().date()
        yesterday = today - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        start_of_year = today.replace(month=1, day=1)
        last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        last_month_end = start_of_month - timedelta(days=1)
        last_year = today.replace(year=today.year - 1, month=1, day=1)

        # Summary stats
        today_orders = orders.filter(created_at__date=today).count()
        week_orders = orders.filter(created_at__date__gte=start_of_week).count()
        month_orders = orders.filter(created_at__date__gte=start_of_month).count()
        year_orders = orders.filter(created_at__date__gte=start_of_year).count()
        pending_orders = orders.filter(order_status="pending").count()

        summary = {
            "today": today_orders,
            "this_week": week_orders,
            "this_month": month_orders,
            "pending": pending_orders,
        }

        # Comparison stats
        yesterday_orders = orders.filter(created_at__date=yesterday).count()
        last_month_orders = orders.filter(
            created_at__date__gte=last_month_start,
            created_at__date__lte=last_month_end
        ).count()
        last_year_orders = orders.filter(
            created_at__date__gte=last_year,
            created_at__date__lt=start_of_year
        ).count()

        def percentage_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 2)

        comparison = {
            "today_vs_yesterday": {
                "current": today_orders,
                "previous": yesterday_orders,
                "change_percent": percentage_change(today_orders, yesterday_orders)
            },
            "month_vs_last_month": {
                "current": month_orders,
                "previous": last_month_orders,
                "change_percent": percentage_change(month_orders, last_month_orders)
            },
            "year_vs_last_year": {
                "current": year_orders,
                "previous": last_year_orders,
                "change_percent": percentage_change(year_orders, last_year_orders)
            }
        }

        # Chart data for last 30 days
        thirty_days_ago = today - timedelta(days=29)
        orders_30 = orders.filter(created_at__date__gte=thirty_days_ago)
        order_counts = orders_30.annotate(date=TruncDate("created_at")).values("date").annotate(count=Count("id"))
        order_map = {item["date"]: item["count"] for item in order_counts}

        chart_data = []
        for i in range(30):
            day = thirty_days_ago + timedelta(days=i)
            chart_data.append({
                "date": day.strftime("%Y-%m-%d"),
                "count": order_map.get(day, 0)
            })

        return Response({
            "store": {
                "id": store.id,
                "name": store.name,
            },
            "summary": summary,
            "comparison": comparison,
            "chart_data": chart_data,
            "query_date_orders": query_date_orders
        })
    
class AdminStoreBookDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        store_id = request.query_params.get("store_id")
        if not store_id:
            return Response({"error": "Missing store_id parameter."}, status=400)

        store = Store.objects.filter(id=store_id).first()
        if not store:
            return Response({"error": "Store not found."}, status=404)

        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        last_30_days = today - timedelta(days=30)

        # --- 1. Sales Summary ---
        def get_summary(start_date):
            orders = Order.objects.filter(
                store=store,
                order_status='completed',
                created_at__date__gte=start_date
            )
            items = OrderItem.objects.filter(order__in=orders)
            total_sold = items.aggregate(total=Sum('quantity'))['total'] or 0
            return {
                "total_sold": total_sold
            }

        sales_summary = {
            "today": get_summary(today),
            "this_week": get_summary(start_of_week),
            "this_month": get_summary(start_of_month),
        }

        # --- 2. Low Stock Books ---
        low_stock_books = Book.objects.filter(
            store=store,
            stock_quantity__lt=5
        ).values("id", "title", "stock_quantity")

        # --- 3. Best Sellers ---
        best_sellers = (
            OrderItem.objects
            .filter(order__store=store, order__order_status="completed")
            .values(book_id_custom=F("book__id"), title=F("book__title"))
            .annotate(sold=Sum("quantity"))
            .order_by("-sold")
        )

        # --- 4. Daily Sales (last 30 days) ---
        daily_sales = (
            Order.objects
            .filter(
                store=store,
                order_status='completed',
                created_at__date__gte=last_30_days
            )
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(
                sold=Sum('items__quantity'),
                revenue=Sum('total_price')
            )
            .order_by('date')
        )

        return Response({
            "sales_summary": sales_summary,
            "low_stock_books": list(low_stock_books),
            "best_sellers": list(best_sellers),
            "daily_sales": list(daily_sales)
        })
    
class AdminStoreTransactionDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        store_id = request.query_params.get("store_id")
        if not store_id:
            return Response({"error": "Missing store_id parameter."}, status=400)

        store = Store.objects.filter(id=store_id).first()
        if not store:
            return Response({"error": "Store not found."}, status=404)

        today = datetime.now().date()
        current_month = today.month
        current_year = today.year

        transactions = Transaction.objects.filter(store=store, status='completed')

        # --- Revenue Totals ---
        today_revenue = transactions.filter(created_at__date=today).aggregate(total=Sum('store_earnings'))['total'] or 0
        month_revenue = transactions.filter(created_at__year=current_year, created_at__month=current_month).aggregate(total=Sum('store_earnings'))['total'] or 0
        year_revenue = transactions.filter(created_at__year=current_year).aggregate(total=Sum('store_earnings'))['total'] or 0

        # --- Transaction Counts ---
        today_count = transactions.filter(created_at__date=today).count()
        month_count = transactions.filter(created_at__year=current_year, created_at__month=current_month).count()
        year_count = transactions.filter(created_at__year=current_year).count()

        # --- Charts ---
        daily_data = (
            transactions
            .annotate(date=TruncDay('created_at'))
            .values('date')
            .annotate(revenue=Sum('store_earnings'))
            .order_by('date')
        )
        monthly_data = (
            transactions
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(revenue=Sum('store_earnings'))
            .order_by('month')
        )
        yearly_data = (
            transactions
            .annotate(year=TruncYear('created_at'))
            .values('year')
            .annotate(revenue=Sum('store_earnings'))
            .order_by('year')
        )

        return Response({
            'totals': {
                'today': {
                    'revenue': today_revenue,
                    'transactions': today_count,
                },
                'this_month': {
                    'revenue': month_revenue,
                    'transactions': month_count,
                },
                'this_year': {
                    'revenue': year_revenue,
                    'transactions': year_count,
                },
            },
            'daily_revenue': [
                {'date': d['date'].strftime('%Y-%m-%d'), 'revenue': float(d['revenue'])}
                for d in daily_data
            ],
            'monthly_revenue': [
                {'month': d['month'].strftime('%Y-%m'), 'revenue': float(d['revenue'])}
                for d in monthly_data
            ],
            'yearly_revenue': [
                {'year': d['year'].year, 'revenue': float(d['revenue'])}
                for d in yearly_data
            ],
        })