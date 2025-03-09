# Generated by Django 5.1.7 on 2025-03-07 01:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applicants', '0003_applicant_document_status_applicant_resume_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Farm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('location', models.CharField(max_length=200)),
                ('specialization', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('capacity', models.IntegerField()),
                ('image', models.ImageField(upload_to='farm_images/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='applicant',
            name='document_status',
        ),
    ]
