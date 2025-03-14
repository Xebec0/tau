# Generated by Django 5.1.7 on 2025-03-14 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applicants', '0010_farm_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicant',
            name='facebook_profile',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='applicant',
            name='instagram_profile',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='applicant',
            name='linkedin_profile',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='applicant',
            name='twitter_profile',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]
