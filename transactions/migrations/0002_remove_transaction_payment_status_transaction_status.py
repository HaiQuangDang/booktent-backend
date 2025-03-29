# Generated by Django 5.1.6 on 2025-03-29 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='payment_status',
        ),
        migrations.AddField(
            model_name='transaction',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('faile', 'Failed'), ('refunded', 'Refunded')], default='pending', max_length=10),
        ),
    ]
