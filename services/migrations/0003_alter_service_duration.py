# Generated by Django 4.2.7 on 2024-06-09 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_alter_service_customer_alter_service_review_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='duration',
            field=models.PositiveIntegerField(),
        ),
    ]
