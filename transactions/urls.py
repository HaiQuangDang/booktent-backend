from django.urls import path
from transactions.views import TransactionListView, TransactionDetailView

urlpatterns = [
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
]
