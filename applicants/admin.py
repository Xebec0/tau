from django.contrib import admin
from .models import Applicant, Farm, FarmApplication
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse, path
from django.shortcuts import redirect
from django.contrib import messages
from django.template.response import TemplateResponse

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = [
        'student_number', 
        'full_name', 
        'gender', 
        'date_of_birth', 
        'created_at', 
        'resume_verification_status', 
        'transcript_verification_status',
        'verify_documents_button'
    ]
    list_filter = [
        'gender', 
        'created_at', 
        'resume_uploaded_at', 
        'transcript_uploaded_at',
        'resume_status',
        'transcript_status'
    ]
    search_fields = ['student_number', 'full_name']
    readonly_fields = [
        'created_at', 
        'resume_uploaded_at', 
        'transcript_uploaded_at', 
        'document_preview',
        'resume_verified_at',
        'resume_verified_by',
        'transcript_verified_at',
        'transcript_verified_by'
    ]
    ordering = ['-created_at']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:applicant_id>/verify-documents/',
                self.admin_site.admin_view(self.verify_documents_view),
                name='verify-documents',
            ),
        ]
        return custom_urls + urls

    def verify_documents_button(self, obj):
        if obj.resume or obj.transcript:
            url = reverse('admin:verify-documents', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" style="background-color: #417690; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">Verify Documents</a>',
                url
            )
        return "No documents"
    verify_documents_button.short_description = 'Document Verification'
    verify_documents_button.allow_tags = True

    def verify_documents_view(self, request, applicant_id):
        applicant = self.get_model_admin(request).get_object(request, applicant_id)
        
        if request.method == 'POST':
            # Handle resume verification
            if 'resume_status' in request.POST:
                applicant.resume_status = request.POST['resume_status']
                applicant.resume_verification_notes = request.POST.get('resume_notes', '')
                applicant.resume_verified_at = timezone.now()
                applicant.resume_verified_by = request.user
            
            # Handle transcript verification
            if 'transcript_status' in request.POST:
                applicant.transcript_status = request.POST['transcript_status']
                applicant.transcript_verification_notes = request.POST.get('transcript_notes', '')
                applicant.transcript_verified_at = timezone.now()
                applicant.transcript_verified_by = request.user
            
            applicant.save()
            messages.success(request, 'Documents verification status updated successfully.')
            return redirect('admin:applicants_applicant_changelist')
        
        context = {
            'title': f'Verify Documents for {applicant.full_name}',
            'applicant': applicant,
            'opts': self.model._meta,
            'document_status_choices': Applicant.DOCUMENT_STATUS_CHOICES,
            'has_resume': bool(applicant.resume),
            'has_transcript': bool(applicant.transcript),
            'original': applicant,
            'media': self.media,
        }
        
        return TemplateResponse(
            request,
            'admin/applicants/verify_documents.html',
            context,
        )

    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'full_name', 'student_number', 'date_of_birth', 'gender', 'country', 'phone_number', 'profile_photo')
        }),
        ('Application Status', {
            'fields': ('status', 'created_at')
        }),
        ('Resume Verification', {
            'fields': (
                'resume',
                'resume_uploaded_at',
                'resume_status',
                'resume_verification_notes',
                'resume_verified_at',
                'resume_verified_by'
            ),
            'classes': ('collapse',),
            'description': 'Verify and manage resume uploads'
        }),
        ('Transcript Verification', {
            'fields': (
                'transcript',
                'transcript_uploaded_at',
                'transcript_status',
                'transcript_verification_notes',
                'transcript_verified_at',
                'transcript_verified_by'
            ),
            'classes': ('collapse',),
            'description': 'Verify and manage transcript uploads'
        }),
        ('Document Preview', {
            'fields': ('document_preview',),
            'description': 'Preview uploaded documents'
        }),
    )

    def resume_verification_status(self, obj):
        status_colors = {
            'pending': 'orange',
            'verified': 'green',
            'rejected': 'red'
        }
        color = status_colors.get(obj.resume_status, 'gray')
        status_text = dict(obj.DOCUMENT_STATUS_CHOICES).get(obj.resume_status, 'Unknown')
        if obj.resume:
            return format_html(
                '<span style="color: {};"><strong>Resume:</strong> ● {}</span>',
                color,
                status_text
            )
        return format_html('<span style="color: gray;">No Resume</span>')
    resume_verification_status.short_description = 'Resume Status'

    def transcript_verification_status(self, obj):
        status_colors = {
            'pending': 'orange',
            'verified': 'green',
            'rejected': 'red'
        }
        color = status_colors.get(obj.transcript_status, 'gray')
        status_text = dict(obj.DOCUMENT_STATUS_CHOICES).get(obj.transcript_status, 'Unknown')
        if obj.transcript:
            return format_html(
                '<span style="color: {};"><strong>Transcript:</strong> ● {}</span>',
                color,
                status_text
            )
        return format_html('<span style="color: gray;">No Transcript</span>')
    transcript_verification_status.short_description = 'Transcript Status'

    def document_preview(self, obj):
        html = ""
        if obj.resume:
            status_color = {
                'pending': 'orange',
                'verified': 'green',
                'rejected': 'red'
            }.get(obj.resume_status, 'gray')
            
            html += f'''
                <div style="margin-bottom: 15px;">
                    <h3 style="margin-bottom: 5px;">Resume</h3>
                    <p><strong>File:</strong> <a href="{obj.resume.url}" target="_blank">{obj.resume.name}</a></p>
                    <p><strong>Status:</strong> <span style="color: {status_color};">● {dict(obj.DOCUMENT_STATUS_CHOICES)[obj.resume_status]}</span></p>
                    <p><strong>Uploaded:</strong> {obj.resume_uploaded_at.strftime("%b %d, %Y at %I:%M %p") if obj.resume_uploaded_at else "N/A"}</p>
                    {f'<p><strong>Verified by:</strong> {obj.resume_verified_by.get_full_name() if obj.resume_verified_by else obj.resume_verified_by}</p>' if obj.resume_verified_by else ""}
                    {f'<p><strong>Verified at:</strong> {obj.resume_verified_at.strftime("%b %d, %Y at %I:%M %p")}</p>' if obj.resume_verified_at else ""}
                </div>
            '''
            
        if obj.transcript:
            status_color = {
                'pending': 'orange',
                'verified': 'green',
                'rejected': 'red'
            }.get(obj.transcript_status, 'gray')
            
            html += f'''
                <div>
                    <h3 style="margin-bottom: 5px;">Transcript</h3>
                    <p><strong>File:</strong> <a href="{obj.transcript.url}" target="_blank">{obj.transcript.name}</a></p>
                    <p><strong>Status:</strong> <span style="color: {status_color};">● {dict(obj.DOCUMENT_STATUS_CHOICES)[obj.transcript_status]}</span></p>
                    <p><strong>Uploaded:</strong> {obj.transcript_uploaded_at.strftime("%b %d, %Y at %I:%M %p") if obj.transcript_uploaded_at else "N/A"}</p>
                    {f'<p><strong>Verified by:</strong> {obj.transcript_verified_by.get_full_name() if obj.transcript_verified_by else obj.transcript_verified_by}</p>' if obj.transcript_verified_by else ""}
                    {f'<p><strong>Verified at:</strong> {obj.transcript_verified_at.strftime("%b %d, %Y at %I:%M %p")}</p>' if obj.transcript_verified_at else ""}
                </div>
            '''
        
        return format_html(html) if html else "No documents uploaded"
    document_preview.short_description = 'Document Preview'

    def save_model(self, request, obj, form, change):
        # Handle resume verification
        if 'resume_status' in form.changed_data:
            obj.resume_verified_at = timezone.now()
            obj.resume_verified_by = request.user

        # Handle transcript verification
        if 'transcript_status' in form.changed_data:
            obj.transcript_verified_at = timezone.now()
            obj.transcript_verified_by = request.user

        super().save_model(request, obj, form, change)

@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'specialization', 'capacity']
    list_filter = ['location', 'specialization']
    search_fields = ['name', 'location', 'specialization']

@admin.register(FarmApplication)
class FarmApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'farm', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('applicant__full_name', 'farm__name')
    date_hierarchy = 'applied_at'