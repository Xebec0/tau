﻿from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.db import transaction, IntegrityError
from .models import Applicant, Farm, FarmApplication
from .forms import (
    ApplicantRegistrationForm,
    AdminRegistrationForm,
    FarmApplicationUpdateForm,
    ProfileUpdateForm
)
from django.urls import reverse

def is_admin(user):
    return user.is_staff or user.is_superuser

def landing_page(request):
    """Landing page view for the application"""
    return render(request, 'applicants/landing.html')

def login_view(request):
    """Custom login view that supports email authentication"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('applicants:dashboard')
            else:
                messages.error(request, "Invalid email/username or password.")
        else:
            messages.error(request, "Invalid email/username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'applicants/login.html', {'form': form})

def role_selection(request):
    """View for selecting registration role (applicant or admin)"""
    return render(request, 'applicants/role_selection.html')

def register_applicant(request):
    # Check for age restriction parameter
    age_restriction = request.GET.get('age_restriction')
    if age_restriction == 'true':
        context = {
            'age_restriction_error': "We're sorry, but applicants must be under 30 years old to apply. You are not eligible for this program.",
            'form': ApplicantRegistrationForm()  # Still pass the form to avoid template errors
        }
        return render(request, 'applicants/register_applicant.html', context)
    
    if request.method == 'POST':
        form = ApplicantRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.save()
                    
                    Applicant.objects.create(
                        user=user,
                        full_name=form.cleaned_data['full_name'],
                        student_number=form.cleaned_data['student_number'],
                        date_of_birth=form.cleaned_data['date_of_birth'],
                        gender=form.cleaned_data['gender'],
                        country=form.cleaned_data['country'],
                        phone_number=form.cleaned_data['phone_number']
                    )
                    
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('applicants:dashboard')
            except IntegrityError:
                messages.error(request, 'This user already has an applicant profile.')
        else:
            # Check for age validation error specifically
            if 'date_of_birth' in form.errors:
                for error in form.errors['date_of_birth']:
                    if "30 years old" in error:
                        # Instead of showing a message, redirect with age restriction parameter
                        return redirect('{}?age_restriction=true'.format(
                            reverse('applicants:register_applicant')
                        ))
    else:
        form = ApplicantRegistrationForm()
    
    return render(request, 'applicants/register_applicant.html', {'form': form})

def register_admin(request):
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                user.is_staff = True
                user.is_superuser = True
                user.save()

                messages.success(request, 'Admin registration successful! Please log in.')
                return redirect('applicants:login')
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
    else:
        form = AdminRegistrationForm()
    
    return render(request, 'applicants/register_admin.html', {'form': form})


@login_required
def dashboard(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('applicants:admin_dashboard')
    
    try:
        applicant = request.user.applicant
        farm_applications = FarmApplication.objects.filter(applicant=applicant)
        
        context = {
            'applicant': applicant,
            'farm_applications': farm_applications,
        }
        return render(request, 'applicants/dashboard.html', context)
    except:
        messages.error(request, 'Please complete your applicant profile first.')
        return redirect('applicants:register_applicant')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    context = {
        'total_applicants': Applicant.objects.count(),
        'pending_applications': Applicant.objects.filter(status='pending').count(),
        'approved_applications': Applicant.objects.filter(status='approved').count(),
        'rejected_applications': Applicant.objects.filter(status='rejected').count(),
        'total_farm_applications': FarmApplication.objects.count(),
        'pending_farm_applications': FarmApplication.objects.filter(status='pending').count(),
        'recent_applications': Applicant.objects.all().order_by('-created_at')[:5],
        'recent_farm_applications': FarmApplication.objects.all().order_by('-applied_at')[:5],
    }
    return render(request, 'applicants/admin_dashboard.html', context)

@login_required
def view_farms(request):
    farms = Farm.objects.all()
    search_query = request.GET.get('search')
    
    if search_query:
        farms = farms.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )
    
    location = request.GET.get('location')
    specialization = request.GET.get('specialization')
    
    if location:
        farms = farms.filter(location=location)
    if specialization:
        farms = farms.filter(specialization=specialization)
    
    context = {
        'farms': farms,
        'locations': Farm.objects.values_list('location', flat=True).distinct(),
        'specializations': Farm.objects.values_list('specialization', flat=True).distinct(),
    }
    return render(request, 'applicants/view_farms.html', context)

@login_required
def farm_detail(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    return render(request, 'applicants/farm_detail.html', {'farm': farm})

@login_required
def apply_to_farm(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    applicant = request.user.applicant
    
    if request.method == 'POST':
        if FarmApplication.objects.filter(applicant=applicant, farm=farm).exists():
            messages.warning(request, 'You have already applied to this farm.')
        else:
            FarmApplication.objects.create(
                applicant=applicant,
                farm=farm,
                motivation_letter=request.POST.get('motivation_letter', '')
            )
            messages.success(request, 'Application submitted successfully!')
        return redirect('applicants:farm_detail', farm_id=farm_id)
    
    return render(request, 'applicants/apply_to_farm.html', {'farm': farm})

@login_required
@user_passes_test(is_admin)
def manage_farm_applications(request):
    applications = FarmApplication.objects.all().order_by('-applied_at')
    status = request.GET.get('status')
    
    if status:
        applications = applications.filter(status=status)
    
    context = {
        'applications': applications,
        'status_choices': FarmApplication.STATUS_CHOICES,
    }
    return render(request, 'applicants/manage_farm_applications.html', context)

@login_required
@user_passes_test(is_admin)
def update_farm_application(request, application_id):
    application = get_object_or_404(FarmApplication, id=application_id)
    
    if request.method == 'POST':
        form = FarmApplicationUpdateForm(request.POST, instance=application)
        if form.is_valid():
            farm_app = form.save(commit=False)
            farm_app.reviewed_by = request.user
            farm_app.reviewed_at = timezone.now()
            farm_app.save()
            messages.success(request, 'Farm application updated successfully!')
            return redirect('applicants:manage_farm_applications')
    else:
        form = FarmApplicationUpdateForm(instance=application)
    
    context = {
        'form': form,
        'application': application,
    }
    return render(request, 'applicants/update_farm_application.html', context)

@login_required
@user_passes_test(is_admin)
def add_farm(request):
    """View for administrators to add new farms"""
    # For GET requests, render the add_farm template
    if request.method != 'POST':
        return render(request, 'applicants/add_farm.html')
        
    try:
        # Extract form data
        name = request.POST.get('name')
        location = request.POST.get('location')
        specialization = request.POST.get('specialization')
        capacity = request.POST.get('capacity')
        description = request.POST.get('description')
        email = request.POST.get('email')
        
        # Create new farm
        farm = Farm(
            name=name,
            location=location,
            specialization=specialization,
            capacity=capacity,
            description=description
        )
        
        # Handle image upload if provided
        if 'image' in request.FILES:
            image = request.FILES['image']
            fs = FileSystemStorage(location='media/farm_images/')
            filename = fs.save(image.name, image)
            farm.image = f'farm_images/{filename}'
        
        farm.save()
        messages.success(request, f'Farm "{name}" has been added successfully!')
        return redirect('applicants:manage_farm_applications')
        
    except Exception as e:
        messages.error(request, f'Error adding farm: {str(e)}')
        return redirect('applicants:manage_farm_applications')

@login_required
def applicant_list(request):
    applicants = Applicant.objects.all()
    return render(request, 'applicants/applicant_list.html', {'applicants': applicants})

@login_required
def applicant_detail(request, student_number):
    applicant = get_object_or_404(Applicant, student_number=student_number)
    return render(request, 'applicants/applicant_detail.html', {'applicant': applicant})

@login_required
@user_passes_test(is_admin)
def delete_applicant(request, student_number):
    applicant = get_object_or_404(Applicant, student_number=student_number)
    if request.method == 'POST':
        applicant.user.delete()
        messages.success(request, 'Applicant deleted successfully.')
        return redirect('applicants:applicant_list')
    return render(request, 'applicants/delete_applicant.html', {'applicant': applicant})

@login_required
def upload_documents(request):
    try:
        applicant = request.user.applicant
    except Applicant.DoesNotExist:
        messages.error(request, 'Please complete your applicant profile first.')
        return redirect('applicants:register_applicant')

    if request.method == 'POST' and request.FILES:
        document_type = request.POST.get('document_type')
        
        if document_type == 'resume':
            if 'resume' in request.FILES:
                file = request.FILES['resume']
                if not file.name.lower().endswith(('.pdf', '.doc', '.docx')):
                    messages.error(request, 'Resume must be a PDF, DOC, or DOCX file.')
                    return render(request, 'applicants/upload_documents.html')
                
                # Check if there's an existing file to replace
                is_replacement = bool(applicant.resume)
                
                # Store the original filename
                original_filename = file.name
                
                # If there's an existing file, it will be automatically deleted by Django
                # when the new file is saved with the same field name
                applicant.resume = file
                applicant.resume_uploaded_at = timezone.now()
                applicant.save()
                
                if is_replacement:
                    messages.success(request, f'Resume "{original_filename}" replaced successfully!')
                else:
                    messages.success(request, f'Resume "{original_filename}" uploaded successfully!')
            else:
                messages.error(request, 'Please select a resume file to upload.')
                
        elif document_type == 'transcript':
            if 'transcript' in request.FILES:
                file = request.FILES['transcript']
                if not file.name.lower().endswith('.pdf'):
                    messages.error(request, 'Transcript must be a PDF file.')
                    return render(request, 'applicants/upload_documents.html')
                
                # Check if there's an existing file to replace
                is_replacement = bool(applicant.transcript)
                
                # Store the original filename
                original_filename = file.name
                
                # If there's an existing file, it will be automatically deleted by Django
                # when the new file is saved with the same field name
                applicant.transcript = file
                applicant.transcript_uploaded_at = timezone.now()
                applicant.save()
                
                if is_replacement:
                    messages.success(request, f'Transcript "{original_filename}" replaced successfully!')
                else:
                    messages.success(request, f'Transcript "{original_filename}" uploaded successfully!')
            else:
                messages.error(request, 'Please select a transcript file to upload.')
        
        return render(request, 'applicants/upload_documents.html')
        
    return render(request, 'applicants/upload_documents.html')

@login_required
def update_profile(request):
    """View for updating user profile"""
    try:
        applicant = request.user.applicant
    except Applicant.DoesNotExist:
        messages.error(request, "You don't have an applicant profile.")
        return redirect('applicants:dashboard')
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=applicant, user=request.user)
        if form.is_valid():
            # Update applicant profile
            profile = form.save(commit=False)
            
            # Handle profile photo upload
            if 'profile_photo' in request.FILES:
                profile.profile_photo = request.FILES['profile_photo']
            
            # Save social media profiles
            profile.linkedin_profile = form.cleaned_data.get('linkedin_profile')
            profile.facebook_profile = form.cleaned_data.get('facebook_profile')
            profile.twitter_profile = form.cleaned_data.get('twitter_profile')
            profile.instagram_profile = form.cleaned_data.get('instagram_profile')
                
            profile.save()
            
            # Update user email
            user = request.user
            user.email = form.cleaned_data['email']
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('applicants:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=applicant, user=request.user)
    
    return render(request, 'applicants/update_profile.html', {'form': form})

@login_required
def contact_support(request):
    if request.method == 'POST':
        # Add support contact logic here
        messages.success(request, 'Support message sent successfully!')
        return redirect('applicants:dashboard')
    return render(request, 'applicants/contact_support.html')

@login_required
@user_passes_test(is_admin)
def review_applications_list(request):
    applications = Applicant.objects.all().order_by('-created_at')
    return render(request, 'applicants/review_applications_list.html', {'applications': applications})

@user_passes_test(is_admin)
def review_application(request, identifier):
    # Try to get the applicant by ID first, then by student number if that fails
    try:
        # First try to convert the identifier to an integer and look up by ID
        applicant_id = int(identifier)
        applicant = get_object_or_404(Applicant, id=applicant_id)
    except (ValueError, TypeError):
        # If conversion fails, assume it's a student number
        applicant = get_object_or_404(Applicant, student_number=identifier)
        
    # Get farm applications for this applicant
    farm_applications = FarmApplication.objects.filter(applicant=applicant)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Applicant.STATUS_CHOICES):
            applicant.status = new_status
            applicant.save()
            messages.success(request, f'Application status updated to {new_status}')
            return redirect('applicants:review_applications_list')
    
    return render(request, 'applicants/review_application.html', {
        'applicant': applicant,
        'farm_applications': farm_applications
    })

@login_required
@user_passes_test(is_admin)
def generate_reports(request):
    """View for generating various reports for admin users"""
    report_type = request.GET.get('type', 'applicants')
    
    # Default data for all reports
    context = {
        'total_applicants': Applicant.objects.count(),
        'pending_applications': Applicant.objects.filter(status='pending').count(),
        'approved_applications': Applicant.objects.filter(status='approved').count(),
        'rejected_applications': Applicant.objects.filter(status='rejected').count(),
        'total_farm_applications': FarmApplication.objects.count(),
        'pending_farm_applications': FarmApplication.objects.filter(status='pending').count(),
        'approved_farm_applications': FarmApplication.objects.filter(status='approved').count(),
        'rejected_farm_applications': FarmApplication.objects.filter(status='rejected').count(),
    }
    
    # Specific data based on report type
    if report_type == 'applicants':
        # Applicants by country
        countries = {}
        for applicant in Applicant.objects.all():
            country = applicant.country
            if country in countries:
                countries[country] += 1
            else:
                countries[country] = 1
        
        # Applicants by gender
        genders = {}
        for applicant in Applicant.objects.all():
            gender = applicant.gender
            if gender in genders:
                genders[gender] += 1
            else:
                genders[gender] = 1
        
        # Applicants by age group
        import datetime
        
        age_groups = {
            '18-20': 0,
            '21-23': 0,
            '24-26': 0,
            '27-30': 0
        }
        
        for applicant in Applicant.objects.all():
            today = timezone.now().date()
            age = today.year - applicant.date_of_birth.year - ((today.month, today.day) < (applicant.date_of_birth.month, applicant.date_of_birth.day))
            
            if age <= 20:
                age_groups['18-20'] += 1
            elif age <= 23:
                age_groups['21-23'] += 1
            elif age <= 26:
                age_groups['24-26'] += 1
            elif age <= 30:
                age_groups['27-30'] += 1
        
        context['countries'] = countries
        context['genders'] = genders
        context['age_groups'] = age_groups
        context['applicants_by_status'] = {
            'Pending': context['pending_applications'],
            'Approved': context['approved_applications'],
            'Rejected': context['rejected_applications']
        }
        
    elif report_type == 'farms':
        # Farm applications by farm
        farms = {}
        for farm in Farm.objects.all():
            farm_apps = FarmApplication.objects.filter(farm=farm).count()
            farms[farm.name] = farm_apps
        
        context['farms'] = farms
        context['farm_applications_by_status'] = {
            'Pending': context['pending_farm_applications'],
            'Approved': context['approved_farm_applications'],
            'Rejected': context['rejected_farm_applications']
        }
    
    context['report_type'] = report_type
    return render(request, 'applicants/generate_reports.html', context)

@login_required
@user_passes_test(is_admin)
def view_all_documents(request):
    """View for admins to see all documents uploaded by applicants"""
    applicants = Applicant.objects.all().order_by('-created_at')
    
    # Filter by document status if requested
    resume_status = request.GET.get('resume_status')
    transcript_status = request.GET.get('transcript_status')
    
    if resume_status:
        applicants = applicants.filter(resume_status=resume_status)
    if transcript_status:
        applicants = applicants.filter(transcript_status=transcript_status)
    
    context = {
        'applicants': applicants,
        'document_status_choices': Applicant.DOCUMENT_STATUS_CHOICES,
        'current_resume_status': resume_status,
        'current_transcript_status': transcript_status,
    }
    return render(request, 'applicants/view_all_documents.html', context)

@login_required
@user_passes_test(is_admin)
def verify_document(request, applicant_id):
    """View for admins to verify applicant documents"""
    applicant = get_object_or_404(Applicant, id=applicant_id)
    
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
        messages.success(request, 'Document verification status updated successfully.')
        return redirect('applicants:view_all_documents')
    
    context = {
        'applicant': applicant,
        'document_status_choices': Applicant.DOCUMENT_STATUS_CHOICES,
    }
    return render(request, 'applicants/verify_document.html', context)

@login_required
@user_passes_test(is_admin)
def update_application_status(request, applicant_id):
    """View for updating an applicant's application status"""
    applicant = get_object_or_404(Applicant, id=applicant_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        if new_status in dict(Applicant.STATUS_CHOICES):
            applicant.status = new_status
            applicant.save()
            messages.success(request, f'Application status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status value')
            
    return redirect('applicants:review_application', identifier=applicant_id)

def privacy_policy(request):
    """
    Display the privacy policy page.
    """
    return render(request, 'applicants/privacy_policy.html')

def terms_of_service(request):
    """
    Display the terms of service page.
    """
    return render(request, 'applicants/terms_of_service.html')

