from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
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
from django.urls import include, path
