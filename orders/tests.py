# order model old version


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

    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    stores = models.ManyToManyField(Store, related_name="orders", blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at the time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.book.title} (Order {self.order.id})"

