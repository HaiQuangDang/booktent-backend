# Generated by Django 5.1.6 on 2025-03-29 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0002_remove_transaction_payment_status_transaction_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin_fee_percentage', models.DecimalField(decimal_places=2, default=10, max_digits=5)),
            ],
        ),
    ]
