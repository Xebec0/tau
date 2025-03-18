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
    first_name = models.CharField(max_length=50, default="DefaultFirstName")
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, default="DefaultLastName")
    student_number = models.CharField(max_length=20, unique=True, default="DEFAULT000")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default="Male")
    country = models.CharField(max_length=100, default='Philippines')
    phone_number = models.CharField(max_length=20, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    
    # Social media fields
    linkedin_profile = models.URLField(max_length=255, blank=True, null=True)
    facebook_profile = models.URLField(max_length=255, blank=True, null=True)
    twitter_profile = models.URLField(max_length=255, blank=True, null=True)
    instagram_profile = models.URLField(max_length=255, blank=True, null=True)
    
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
        full_name = f"{self.first_name}"
        if self.middle_name:
            full_name += f" {self.middle_name}"
        full_name += f" {self.last_name}"
        return f"{full_name} ({self.student_number})"
    
    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

class Farm(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    specialization = models.CharField(max_length=100)
    capacity = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='farm_images/', null=True, blank=True)
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
    motivation_letter = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.applicant.full_name} - {self.farm.name}"


class Document(models.Model):
    """Model for applicant documents with enhanced management capabilities"""
    DOCUMENT_TYPES = [
        ('resume', 'Resume'),
        ('transcript', 'Academic Transcript'),
        ('passport', 'Passport'),
        ('medical_certificate', 'Medical Certificate'),
        ('recommendation_letter', 'Recommendation Letter'),
        ('other', 'Other Document')
    ]
    
    # Dictionary for easy access to document type names
    DOCUMENT_TYPES_DICT = dict(DOCUMENT_TYPES)
    
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ]
    
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='applicant_documents/')
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=100, help_text="MIME type of the file")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verification_notes = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        unique_together = ['applicant', 'document_type']  # One document type per applicant
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.applicant.full_name}"
    
    @property
    def file_extension(self):
        """Return the file extension"""
        return self.original_filename.split('.')[-1] if '.' in self.original_filename else ''
    
    @property
    def file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024 or unit == 'GB':
                return f"{size:.2f} {unit}"
            size /= 1024


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('document_reminder', 'Document Reminder'),
        ('application_status', 'Application Status Update'),
        ('general', 'General Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"