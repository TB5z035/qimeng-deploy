# Generated by Django 4.1.4 on 2022-12-19 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0002_remove_detectionrequest_order_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detectionrequest',
            name='search_key',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
