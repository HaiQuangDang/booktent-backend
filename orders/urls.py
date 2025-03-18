from django.urls import path
from .views import OrderViewSet, UpdateOrderStatusView, StripeCheckoutSessionView, StoreOrderDetailView
from .views import payment_success, stripe_webhook

urlpatterns = [
    path('create/', OrderViewSet.as_view({'post': 'create'}), name='order_create'),
    path('list/', OrderViewSet.as_view({'get': 'list'}), name='order_list'),
    path('retrieve/<int:pk>/', OrderViewSet.as_view({'get': 'retrieve'}), name='order_detail'),
    path("stripe/create-checkout-session/", StripeCheckoutSessionView.as_view(), name="create-checkout-session"),
    path("payment-success/", payment_success, name="payment-success"),
    path("webhook/", stripe_webhook, name="stripe-webhook"),
    # for store owner
    path("my-store/", OrderViewSet.as_view({"get": "my_store_orders"}), name="my_store_orders"),
    path("update-status/<int:pk>/", UpdateOrderStatusView.as_view(), name="update_order_status"),
    path("my-store/<int:order_id>/", StoreOrderDetailView.as_view(), name="store-order-detail"),

]
