from rest_framework import serializers
from .models import Store

class StoreSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")  # Show owner's username

    class Meta:
        model = Store
        fields = ["id", "name", "description", "owner", "logo", "created_at", "updated_at", "status", "contact_info"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]  # Owner is set automatically
