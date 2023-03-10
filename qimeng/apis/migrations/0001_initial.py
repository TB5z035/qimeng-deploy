# Generated by Django 4.1.4 on 2022-12-18 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DetectionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('station_id', models.CharField(max_length=50)),
                ('status',
                 models.CharField(
                     choices=[('SUBMITTED', 'SUBMITTED'), ('RUNNING', 'RUNNING'), ('FINISHED', 'FINISHED'),
                              ('ERROR', 'ERROR')],
                     default='SUBMITTED',
                     max_length=50)),
                ('image', models.ImageField(upload_to='saved_images/%Y/%m/%d')),
                ('search_key', models.CharField(blank=True, max_length=200)),
                ('order_id', models.CharField(blank=True, max_length=20)),
            ],
        ),
    ]
