from rest_framework import generics, permissions, serializers
from .models import Store
from .serializers import StoreSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from books.models import Book
from django.utils import timezone
from datetime import timedelta, datetime
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, F
from decimal import Decimal
from orders.models import Order
from django.db.models.functions import TruncDate, TruncDay, TruncMonth, TruncYear
from transactions.models import Transaction
from backend.admin_views import StandardResultsSetPagination
from orders.models import OrderItem
from django.utils.timezone import now

class StoreListCreateView(generics.ListCreateAPIView):
    serializer_class = StoreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination  # Add pagination class

    def get_queryset(self):
        queryset = Store.objects.all().order_by("-created_at")
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        if Store.objects.filter(owner=self.request.user).exists():
            raise serializers.ValidationError({"detail": "You already have a store."})
        serializer.save(owner=self.request.user) # Set the store owner to the logged-in user

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
            # ✅ Pass context={"request": request}
            return Response(StoreSerializer(store, context={"request": request}).data)
        except Store.DoesNotExist:
            return Response({"detail": "No store found"})

# Store Dashboard
class StoreDashboardView(APIView):
    """Dashboard API for store owners to see an overview of their store"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure the user is a store owner
        store = Store.objects.filter(owner=request.user).first()
        if not store:
            return Response({"error": "You do not own a store."}, status=403)

        # Total Orders
        total_orders = Order.objects.filter(store=store).count()

        # Total Earnings (only from completed orders)
        total_earnings = Transaction.objects.filter(
            store=store, status="completed"
        ).aggregate(total=Sum("store_earnings"))["total"] or Decimal("0.00")

        # Total Books (all books in store)
        total_books = store.books.count()

        # Low Stock Books (stock < 5)
        low_stock_books = list(
            store.books.filter(stock_quantity__lt=5).values("title", "stock_quantity")
        )

        # Recent Orders (last 5)
        recent_orders = list(
            Order.objects.filter(store=store)
            .order_by("-created_at")[:5]
            .values("id", "total_price", "order_status", "created_at")
        )

        # Recent Books (last 5 added)
        recent_books = list(
            store.books.order_by("-created_at")[:5].values("id", "title", "price", "stock_quantity")
        )

        # Recent Transactions (last 5)
        recent_transactions = list(
            Transaction.objects.filter(store=store, status="completed")
            .order_by("-created_at")[:5]
            .values("id", "amount", "status", "created_at")
        )

        # Return all data in one response
        return Response({
            "store_name": store.name,
            "store_status": store.status,
            "total_orders": total_orders,
            "total_earnings": float(total_earnings),  # Convert Decimal to float for JSON
            "total_books": total_books,
            "low_stock_books": low_stock_books,
            "recent_orders": recent_orders,
            "recent_books": recent_books,
            "recent_transactions": recent_transactions
        })

# Store Order Dashboard
class StoreOrderDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        store = Store.objects.filter(owner=user).first()
        if not store:
            return Response({"error": "You do not own a store."}, status=403)

        orders = Order.objects.filter(store=store)

        query_date_str = request.query_params.get("date")
        query_date_orders = None
        if query_date_str:
            try:
                query_date = datetime.strptime(query_date_str, "%Y-%m-%d").date()
                query_date_orders = orders.filter(created_at__date=query_date).count()
            except ValueError:
                query_date_orders = "Invalid date format. Use YYYY-MM-DD."

        # --- Time Setup ---
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)
        start_of_year = today.replace(month=1, day=1)
        last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        last_month_end = start_of_month - timedelta(days=1)
        last_year = today.replace(year=today.year - 1, month=1, day=1)

        # --- Summary Stats ---
        today_orders = orders.filter(created_at__date=today).count()
        week_orders = orders.filter(created_at__date__gte=start_of_week).count()
        month_orders = orders.filter(created_at__date__gte=start_of_month).count()
        year_orders = orders.filter(created_at__date__gte=start_of_year).count()
        pending_orders = orders.filter(order_status="pending").count()

        summary = {
            "today": today_orders,
            "this_week": week_orders,
            "this_month": month_orders,
            # "this_year": year_orders,
            "pending": pending_orders,
        }

        # --- Comparison Stats ---
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

        # --- Chart Data: Last 30 Days ---
        thirty_days_ago = today - timedelta(days=29)

        # Get all orders in the last 30 days
        orders_30 = orders.filter(created_at__date__gte=thirty_days_ago)

        # Count orders per day
        order_counts = orders_30.annotate(date=TruncDate("created_at")).values("date").annotate(count=Count("id"))

        # Convert to a dictionary for fast lookup
        order_map = {item["date"]: item["count"] for item in order_counts}

        # Generate 30-day range and fill in missing days with count = 0
        chart_data = []
        for i in range(30):
            day = thirty_days_ago + timedelta(days=i)
            chart_data.append({
                "date": day.strftime("%Y-%m-%d"),
                "count": order_map.get(day, 0)
            })

        return Response({
            "summary": summary,
            "comparison": comparison,
            "chart_data": chart_data,
            "query_date_orders": query_date_orders 
        })

# Store Book Dashboard
class StoreBookDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        store = Store.objects.filter(owner=user).first()
        if not store:
            return Response({"error": "You do not own a store."}, status=403)
       
        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        start_of_month = today.replace(day=1)
        last_30_days = today - timedelta(days=30)

        # 1. Sales Summary
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

        # 2. Low Stock Books
        low_stock_books = Book.objects.filter(
            store=store,
            stock_quantity__lt=5
        ).values("id", "title", "stock_quantity")

        # 3. Best Sellers
        best_sellers = (
            OrderItem.objects
            .filter(order__store=store, order__order_status="completed")
            .values(book_id_custom=F("book__id"), title=F("book__title"))  # ✅ safe key names
            .annotate(sold=Sum("quantity"))
            .order_by("-sold")
        )

        # 4. Daily Sales (last 30 days)
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
    
# Store Transaction Dashboard
class StoreTransactionDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        store = Store.objects.filter(owner=user).first()
        if not store:
            return Response({"error": "You do not own a store."}, status=403)

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