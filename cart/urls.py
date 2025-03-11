from django.urls import path
from .views import CartViewSet

cart_view = CartViewSet.as_view({
    'get': 'list',
    'post': 'add_to_cart',
})

urlpatterns = [
    path('', cart_view, name="cart-list"),
    path('update/<int:pk>/', CartViewSet.as_view({'put': 'update_quantity'}), name="cart-update"),
    path('remove/<int:pk>/', CartViewSet.as_view({'delete': 'remove_from_cart'}), name="cart-remove"),
    path('clear/', CartViewSet.as_view({'delete': 'clear_cart'}), name="cart-clear"),
    path('check/<int:pk>/', CartViewSet.as_view({'get': 'check'}), name='check_book_in_cart'),
]
