from django.db import models
from django.contrib.auth.models import User
from books.models import Book
from stores.models import Store
from django.conf import settings

class Order(models.Model):
    ORDER_STATUS = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("completed", "Completed"),
        ("canceled", "Canceled"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_METHODS = [
        ('online', 'Online Payment'),
        ('cod', 'Cash on Delivery'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='cod')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    order_status = models.CharField(max_length=10, choices=ORDER_STATUS, default='pending')
    address = models.TextField(blank=True, null=True)  # 🆕 Added address field
    phone = models.CharField(max_length=20, blank=True, null=True)  # 🆕 Added phone field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        store_name = self.store.name if self.store else "No Store"
        return f"Order {self.id} - {store_name} - {self.order_status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.PROTECT)  # Can't delete book if linked to orders
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Snapshot of book price at purchase

    def __str__(self):
        return f"{self.quantity} x {self.book.title} (Order {self.order.id})"
