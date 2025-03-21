from django.urls import path
from transactions.views import TransactionListView, TransactionDetailView

urlpatterns = [
    path("list/", TransactionListView.as_view(), name="transaction-list"),
    path("<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
]
