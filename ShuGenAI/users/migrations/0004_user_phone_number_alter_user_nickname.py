# Generated by Django 5.1.1 on 2024-11-04 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_card"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="phone_number",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="nickname",
            field=models.CharField(blank=True, max_length=14, null=True),
        ),
    ]
