from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Applicant(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    DOCUMENT_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    student_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    country = models.CharField(max_length=100, default='Philippines')
    phone_number = models.CharField(max_length=20, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    
    # Document fields
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    resume_uploaded_at = models.DateTimeField(null=True, blank=True)
    resume_status = models.CharField(max_length=20, choices=DOCUMENT_STATUS_CHOICES, default='pending')
    resume_verified_at = models.DateTimeField(null=True, blank=True)
    resume_verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_resumes')
    resume_verification_notes = models.TextField(blank=True)
    
    transcript = models.FileField(upload_to='transcripts/', null=True, blank=True)
    transcript_uploaded_at = models.DateTimeField(null=True, blank=True)
    transcript_status = models.CharField(max_length=20, choices=DOCUMENT_STATUS_CHOICES, default='pending')
    transcript_verified_at = models.DateTimeField(null=True, blank=True)
    transcript_verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_transcripts')
    transcript_verification_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.student_number})"

class Farm(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    specialization = models.CharField(max_length=100)
    capacity = models.IntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class FarmApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    applicant = models.ForeignKey('Applicant', on_delete=models.CASCADE)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.full_name} - {self.farm.name}"