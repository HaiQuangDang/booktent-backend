from django.urls import path
from .views import OrderViewSet

urlpatterns = [
    path('create/', OrderViewSet.as_view({'post': 'create'}), name='order_create'),
    path('list/', OrderViewSet.as_view({'get': 'list'}), name='order_list'),
    path('retrieve/<int:pk>/', OrderViewSet.as_view({'get': 'retrieve'}), name='order_detail'),
    path('payment/<int:pk>/confirm/', OrderViewSet.as_view({'post': 'confirm_payment'}), name='confirm_payment'),
]
