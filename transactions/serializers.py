from rest_framework import serializers
from transactions.models import Transaction, SiteConfig

class TransactionSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)  # Get store name
    user_id = serializers.IntegerField(source="order.user.id", read_only=True)  # Get user ID
    user_name = serializers.CharField(source="order.user.username", read_only=True)  # Get user name

    class Meta:
        model = Transaction
        fields = "__all__"  # Include all fields + store_name, user_id, user_name


class SiteConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteConfig
        fields = ["admin_fee_percentage"]
