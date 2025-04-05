from django.db import models
from django.contrib.auth.models import User

class GenreRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)  # Optional
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="genre_requests")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)  # When admin reviews it

    def __str__(self):
        return f"{self.name} ({self.status})"

class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)  # Optional
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

