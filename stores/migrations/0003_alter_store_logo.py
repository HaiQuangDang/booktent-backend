# Generated by Django 5.1.6 on 2025-03-09 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0002_alter_store_logo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='logo',
            field=models.ImageField(default='stores/BookTent.png', upload_to='stores/'),
        ),
    ]
