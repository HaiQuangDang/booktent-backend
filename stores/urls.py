from django.urls import path
from .views import StoreListCreateView, StoreDetailView, MyStoreView

urlpatterns = [
    path("", StoreListCreateView.as_view(), name="store-list-create"),
    path("<int:pk>/", StoreDetailView.as_view(), name="store-detail"),
    path("mine/", MyStoreView.as_view(), name="my-store"),
]
