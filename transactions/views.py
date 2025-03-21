from rest_framework import generics, permissions
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer

class IsAdminOrStoreOwner(permissions.BasePermission):
    """Allow only admin or store owners to access transactions."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_staff or hasattr(request.user, "store"))

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.store.owner == request.user

class TransactionListView(generics.ListAPIView):
    """Admin gets all transactions, store owners get their own transactions."""
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminOrStoreOwner]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Transaction.objects.all()  # Admin gets all
        return Transaction.objects.filter(store__owner=user)  # Store owner gets only theirs

class TransactionDetailView(generics.RetrieveAPIView):
    """Allows admin and store owners to see transaction details."""
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminOrStoreOwner]
    queryset = Transaction.objects.all()
