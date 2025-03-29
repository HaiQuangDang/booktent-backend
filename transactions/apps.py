from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_default_site_config(sender, **kwargs):
    """Ensure a default SiteConfig entry exists after migrations."""
    if sender.name == "transactions":  # Replace with your actual app name
        from .models import SiteConfig  # Import inside function to avoid early DB access
        SiteConfig.objects.get_or_create(defaults={"admin_fee_percentage": 10.0})

class TransactionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "transactions"

    def ready(self):
        post_migrate.connect(create_default_site_config, sender=self)
