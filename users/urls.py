
from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .token import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="get_token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("register/", views.CreateUserView.as_view(), name="register"),
    path("delete/<int:pk>/", views.DeleteUserView.as_view(), name='delete-user'),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user-detail"),
    path("admin-check/", views.AdminCheckView.as_view(), name="admin-check"),
    path("users/", views.ListUsersView.as_view(), name="list-users"),

]