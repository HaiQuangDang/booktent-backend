from django.urls import path
from .views import StoreListCreateView, StoreDetailView, MyStoreView, StoreDashboardView
from .views import StoreOrderDashboardView, StoreBookDashboardView, StoreTransactionDashboardView

urlpatterns = [
    path("", StoreListCreateView.as_view(), name="store-list-create"),
    path("<int:pk>/", StoreDetailView.as_view(), name="store-detail"),
    path("mine/", MyStoreView.as_view(), name="my-store"),
    path("dashboard/", StoreDashboardView.as_view(), name="store-dashboard"),
    path("dashboard/orders/", StoreOrderDashboardView.as_view(), name="store-order-dashboard"),
    path("dashboard/books/", StoreBookDashboardView.as_view(), name="store-book-dashboard"),
    path("dashboard/transactions/", StoreTransactionDashboardView.as_view(), name="store-transaction-dashboard"),
]
