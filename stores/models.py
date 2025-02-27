from django.db import models
from django.conf import settings

class Store(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("pending", "Pending"),
        ("suspended", "Suspended"),
    ]

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    logo = models.ImageField(upload_to="store_logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    contact_info = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name
