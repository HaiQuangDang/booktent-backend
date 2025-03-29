from django.apps import AppConfig
from django.core.exceptions import ObjectDoesNotExist

class TransactionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "transactions"

    def ready(self):
        from transactions.models import SiteConfig
        try:
            SiteConfig.objects.get()
        except ObjectDoesNotExist:
            SiteConfig.objects.create(admin_fee_percentage=10)  # Default 10%

