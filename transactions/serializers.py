from rest_framework import serializers
from transactions.models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)  # Get store name

    class Meta:
        model = Transaction
        fields = "__all__"  # Include all fields + store_name
