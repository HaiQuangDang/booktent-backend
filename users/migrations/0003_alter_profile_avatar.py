# Generated by Django 5.1.6 on 2025-03-10 07:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_profile_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(default='avatars/defaultuser.jpg', upload_to='avatars/'),
        ),
    ]
