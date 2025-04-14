from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

# Admin views
from .admin_views import (
    admin_stats,
    recent_activity,
    earnings_stats,
    admin_fee_view,
    admin_book_stats,
    recent_authors,
    genre_requests,
    AdminBookListView,
    AdminUpdateBookStatusView,
    AdminDeleteBookView,
    AdminOrderListView,
    AdminOrderDetailView,
    AdminStoreOrderDashboardView,
    AdminStoreBookDashboardView,
    AdminStoreTransactionDashboardView,
    GenreRequestAdminViewSet
)

# Routers
adminGenresRequest = DefaultRouter()
adminGenresRequest.register(r'admin/genres-request', GenreRequestAdminViewSet, basename="genre-request-admin")

urlpatterns = [
    # Django Admin
    # path("admin/", admin.site.urls),

    # Admin Custom Views
    path("admin/stats/", admin_stats, name="admin-stats"),
    path("admin/recent-activity/", recent_activity, name="admin-recent-activity"),
    path("admin/earnings/", earnings_stats, name="admin-earnings"),
    path("admin/book-stats/", admin_book_stats, name="admin-book-stats"),
    path("admin/recent-authors/", recent_authors, name="admin-recent-authors"),
    path("admin/recent-genre-requests/", genre_requests, name="admin-genre-requests"),
    path("admin-fee/", admin_fee_view, name="admin-fee"),

    # Admin Book Management
    path("admin/books/", AdminBookListView.as_view(), name="admin-books"),
    path("admin/books/<int:pk>/status/", AdminUpdateBookStatusView.as_view(), name="admin-update-book-status"),
    path("admin/books/<int:pk>/delete/", AdminDeleteBookView.as_view(), name="admin-delete-book"),

    # Admin Order Management
    path("admin/orders/", AdminOrderListView.as_view(), name="admin-orders-list"),
    path("admin/orders/<int:pk>/", AdminOrderDetailView.as_view(), name="admin-order-detail"),

    # Admin Store Dashboards
    path("admin/store-orders/", AdminStoreOrderDashboardView.as_view(), name="admin-store-orders"),
    path("admin/store-books/", AdminStoreBookDashboardView.as_view(), name="admin-store-books"),
    path("admin/store-transactions/", AdminStoreTransactionDashboardView.as_view(), name="admin-store-transactions"),

    # Admin Routers
    path('', include(adminGenresRequest.urls)),

    # App Includes
    path("authentication/", include("rest_framework.urls")),
    path("books/", include("books.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("stores/", include("stores.urls")),
    path("transactions/", include("transactions.urls")),
    path("user/", include("users.urls")),
]

# Media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
