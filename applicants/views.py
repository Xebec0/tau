from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.db.models import Q

from .models import Applicant, Farm, FarmApplication
from .forms import (
    ApplicantRegistrationForm,
    AdminRegistrationForm,
    FarmApplicationUpdateForm
)

def is_admin(user):
    return user.is_staff or user.is_superuser

def landing_page(request):
    """Landing page view for the application"""
    return render(request, 'applicants/landing.html')

def role_selection(request):
    """View for selecting registration role (applicant or admin)"""
    return render(request, 'applicants/role_selection.html')

def register_applicant(request):
    if request.method == 'POST':
        form = ApplicantRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create associated Applicant profile
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
    
    applicant = request.user.applicant
    farm_applications = FarmApplication.objects.filter(applicant=applicant)
    
    context = {
        'applicant': applicant,
        'farm_applications': farm_applications,
    }
    return render(request, 'applicants/dashboard.html', context)

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
    if request.method == 'POST' and request.FILES:
        fs = FileSystemStorage()
        for uploaded_file in request.FILES.values():
            fs.save(uploaded_file.name, uploaded_file)
        messages.success(request, 'Documents uploaded successfully!')
        return redirect('applicants:dashboard')
    return render(request, 'applicants/upload_documents.html')

@login_required
def update_profile(request):
    if request.method == 'POST':
        # Add profile update logic here
        messages.success(request, 'Profile updated successfully!')
        return redirect('applicants:dashboard')
    return render(request, 'applicants/update_profile.html')

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

@login_required
@user_passes_test(is_admin)
def review_application(request, student_number):
    applicant = get_object_or_404(Applicant, student_number=student_number)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Applicant.STATUS_CHOICES):
            applicant.status = new_status
            applicant.save()
            messages.success(request, f'Application status updated to {new_status}')
            return redirect('applicants:review_applications_list')
    return render(request, 'applicants/review_application.html', {'applicant': applicant})
