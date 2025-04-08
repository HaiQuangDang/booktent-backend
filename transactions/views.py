from rest_framework import generics, permissions
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer
from backend.admin_views import StandardResultsSetPagination

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
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        # Base queryset based on user role
        if user.is_staff:
            queryset = Transaction.objects.all()  # Admin gets all
        else:
            queryset = Transaction.objects.filter(store__owner=user)  # Store owner gets theirs

        # Apply filters from query parameters
        status = self.request.query_params.get("status", None)
        payment_method = self.request.query_params.get("payment_method", None)

        if status:
            queryset = queryset.filter(status=status)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        # Default sorting by created_at descending (newest first)
        return queryset.order_by("-created_at")
    
class TransactionDetailView(generics.RetrieveAPIView):
    """Allows admin and store owners to see transaction details."""
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminOrStoreOwner]
    queryset = Transaction.objects.all()
