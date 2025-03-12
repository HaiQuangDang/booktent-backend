from django.db import models
from django.contrib.auth.models import User
from books.models import Book
from stores.models import Store 

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),        # Order placed
        ("processing", "Processing"),  # Order being prepared
        ("shipped", "Shipped"),        # Order sent out (if delivery exists)
        ("completed", "Completed"),    # Order received successfully
        ("canceled", "Canceled"),      # Order was canceled
        ("refunded", "Refunded"),      # Order refunded (if needed)
    ]

    PAYMENT_METHODS = [
        ("paypal", "PayPal"),
        ("stripe", "Stripe"),
        ("cod", "Cash on Delivery"),  # Offline payment
    ]

    PAYMENT_STATUSES = [
        ("pending", "Pending"),   # Waiting for user payment
        ("paid", "Paid"),         # Payment completed successfully
        ("failed", "Failed"),     # Payment failed
        ("refunded", "Refunded"), # Payment refunded
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    stores = models.ManyToManyField(Store, related_name="orders", blank=True)
    
    # New fields for online payments
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default="cod")
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUSES, default="pending")

    def __str__(self):
        return f"Order {self.id} - {self.user.username} - {self.payment_method} - {self.payment_status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.book.title} (Order {self.order.id})"
