from django.urls import path
from .views import OrderViewSet
from .views import StoreOrderViewSet
from .views import StoreOrderUpdateStatusView

urlpatterns = [
    path("create/",  OrderViewSet.as_view({"post": "create"})),
    path("list/", OrderViewSet.as_view({"get": "list"})),
    path("list/<int:pk>/", OrderViewSet.as_view({"get": "retrieve"})),  
    path("cancel/<int:pk>/", OrderViewSet.as_view({"post": "cancel"}), name="cancel_order"),
    path("store/orders/", StoreOrderViewSet.as_view({"get": "list"})), 
    path("store/update-status/<int:order_id>/", StoreOrderUpdateStatusView.as_view(), name="store-update-status"),
]