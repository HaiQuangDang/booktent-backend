from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("authentication/", include("rest_framework.urls")),
    path("user/", include("users.urls")),
    path("store/", include("stores.urls")),
    path("books/", include("books.urls")),
]