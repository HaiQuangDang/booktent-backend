# Generated by Django 5.1.6 on 2025-04-06 03:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_order_stripe_session_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
