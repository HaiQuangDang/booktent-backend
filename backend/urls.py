from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from .admin_views import admin_stats, recent_activity, earnings_stats, admin_fee_view
from .admin_views import AdminBookListView, AdminUpdateBookStatusView, AdminDeleteBookView
from .admin_views import AdminOrderListView, AdminOrderDetailView
from .admin_views import GenreRequestAdminViewSet, recent_authors, genre_requests  # Import new views

adminGenresRequest = DefaultRouter()
adminGenresRequest.register(r'admin/genres-request', GenreRequestAdminViewSet, basename="genre-request-admin")

urlpatterns = [
    path("admin/stats/", admin_stats, name="admin-stats"),
    path("admin/recent-activity/", recent_activity, name="admin-recent-activity"),
    path("admin/earnings/", earnings_stats, name="admin-earnings"),
    path("admin/books/", AdminBookListView.as_view(), name="admin-books"),
    path("admin/books/<int:pk>/status/", AdminUpdateBookStatusView.as_view(), name="admin-update-book-status"),
    path("admin/books/<int:pk>/delete/", AdminDeleteBookView.as_view(), name="admin-delete-book"),
    path("admin/orders/", AdminOrderListView.as_view(), name="admin-orders-list"),
    path("admin/orders/<int:pk>/", AdminOrderDetailView.as_view(), name="admin-order-detail"),
    path("admin-fee/", admin_fee_view, name="admin-fee"),
    path("admin/recent-authors/", recent_authors, name="admin-recent-authors"),
    path("admin/recent-genre-requests/", genre_requests, name="admin-genre-requests"),
    path('', include(adminGenresRequest.urls)),

    path("admin/", admin.site.urls),
    path("authentication/", include("rest_framework.urls")),
    path("user/", include("users.urls")),
    path("stores/", include("stores.urls")),
    path("books/", include("books.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("transactions/", include("transactions.urls"))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
