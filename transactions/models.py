from django.db import models
from orders.models import Order
from stores.models import Store

class Transaction(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('faile', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='transaction')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    admin_fee = models.DecimalField(max_digits=10, decimal_places=2)
    store_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction for Order {self.order.id} - {self.status}"


class SiteConfig(models.Model):
    admin_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10)

    def __str__(self):
        return f"Admin Fee: {self.admin_fee_percentage}%"

    @classmethod
    def get_admin_fee(cls):
        config, _ = cls.objects.get_or_create(id=1)  # Ensure there's always one config entry
        return config.admin_fee_percentage / 100  # Convert to decimal
