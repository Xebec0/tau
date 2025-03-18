# Generated by Django 5.1.7 on 2025-03-17 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applicants', '0011_applicant_facebook_profile_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='applicant',
            name='full_name',
        ),
        migrations.AddField(
            model_name='applicant',
            name='first_name',
            field=models.CharField(default='DefaultFirstName', max_length=50),
        ),
        migrations.AddField(
            model_name='applicant',
            name='last_name',
            field=models.CharField(default='DefaultLastName', max_length=50),
        ),
        migrations.AddField(
            model_name='applicant',
            name='middle_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='applicant',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='applicant',
            name='gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female')], default='Male', max_length=6),
        ),
        migrations.AlterField(
            model_name='applicant',
            name='student_number',
            field=models.CharField(default='DEFAULT000', max_length=20, unique=True),
        ),
    ]
