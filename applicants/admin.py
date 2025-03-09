from django.contrib import admin
from .models import Applicant, Farm, FarmApplication

@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['student_number', 'full_name', 'gender', 'date_of_birth', 'created_at']
    list_filter = ['gender', 'created_at']
    search_fields = ['student_number', 'full_name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


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