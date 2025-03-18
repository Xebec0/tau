from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from .models import Applicant, Farm, FarmApplication, Notification, Document
from .forms import (
    ApplicantRegistrationForm,
    AdminRegistrationForm,
    FarmApplicationUpdateForm,
    ProfileUpdateForm
)
from django.urls import reverse
import os

def is_admin(user):
    return user.is_staff or user.is_superuser

def landing_page(request):
    """Landing page view for the application"""
    # Redirect already authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('applicants:dashboard')
        
    return render(request, 'applicants/landing.html')

def login_view(request):
    """Custom login view that supports email authentication"""
    # Redirect already authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('applicants:dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
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
    # Redirect already authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('applicants:dashboard')
        
    return render(request, 'applicants/role_selection.html')

def register_applicant(request):
    print("DEBUG: Entering register_applicant view")
    # Redirect already authenticated users to dashboard
    if request.user.is_authenticated:
        print(f"DEBUG: User {request.user.username} is authenticated, redirecting to dashboard")
        return redirect('applicants:dashboard')
        
    # Check for age restriction parameter
    age_restriction = request.GET.get('age_restriction')
    if age_restriction == 'true':
        print("DEBUG: Age restriction parameter is true")
        context = {
            'age_restriction_error': "We're sorry, but applicants must be under 30 years old to apply. You are not eligible for this program.",
            'form': ApplicantRegistrationForm()  # Still pass the form to avoid template errors
        }
        return render(request, 'applicants/register_applicant.html', context)
    
    if request.method == 'POST':
        print("DEBUG: Processing POST request")
        form = ApplicantRegistrationForm(request.POST)
        if form.is_valid():
            print("DEBUG: Form is valid")
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.save()
                    
                    Applicant.objects.create(
                        user=user,
                        first_name=form.cleaned_data['first_name'],
                        middle_name=form.cleaned_data['middle_name'],
                        last_name=form.cleaned_data['last_name'],
                        student_number=form.cleaned_data['student_number'],
                        date_of_birth=form.cleaned_data['date_of_birth'],
                        gender=form.cleaned_data['gender'],
                        phone_number=form.cleaned_data['phone_number']
                    )
                print("DEBUG: User and applicant created successfully")
                    
                # Authenticate and login the user with the ModelBackend
                authenticated_user = authenticate(request, username=user.username, password=form.cleaned_data['password1'])
                if authenticated_user is not None:
                    print("DEBUG: User authenticated successfully")
                    login(request, authenticated_user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, 'Registration successful!')
                    return redirect('applicants:dashboard')
                else:
                    print("DEBUG: User authentication failed")
                    messages.error(request, 'Authentication failed after registration.')
                return redirect('applicants:login')
            except IntegrityError:
                print("DEBUG: IntegrityError occurred")
                messages.error(request, 'This user already has an applicant profile.')
        else:
            print(f"DEBUG: Form is invalid. Errors: {form.errors}")
            # Check for age validation error specifically
            if 'date_of_birth' in form.errors:
                for error in form.errors['date_of_birth']:
                    if "30 years old" in error:
                        # Instead of showing a message, redirect with age restriction parameter
                        print("DEBUG: Age validation error, redirecting with age_restriction=true")
                        return redirect('{}?age_restriction=true'.format(
                            reverse('applicants:register_applicant')
                        ))
    else:
        print("DEBUG: GET request, creating empty form")
        form = ApplicantRegistrationForm()
    
    return render(request, 'applicants/register_applicant.html', {'form': form})

def register_admin(request):
    # Redirect already authenticated users to dashboard
    if request.user.is_authenticated:
        return redirect('applicants:dashboard')
        
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
    print("DEBUG: Entering dashboard view")
    if request.user.is_staff or request.user.is_superuser:
        print("DEBUG: User is staff/admin, redirecting to admin_dashboard")
        return redirect('applicants:admin_dashboard')
    
    try:
        print(f"DEBUG: Trying to get applicant for user {request.user.username}")
        applicant = request.user.applicant
        print(f"DEBUG: Successfully got applicant {applicant.id}")
        farm_applications = FarmApplication.objects.filter(applicant=applicant)
    
        # Add messages based on application status
        if applicant.status == 'pending':
            if not hasattr(request, '_messages') or not any(m.message == 'Your application is currently under review.' for m in request._messages):
                messages.info(request, 'Your application is currently under review.')
        elif applicant.status == 'rejected':
            if not hasattr(request, '_messages') or not any(m.message == 'Your application has been rejected.' for m in request._messages):
                messages.error(request, 'Your application has been rejected. Please contact support for more information.')
        
        # Create a test notification if there are no notifications yet
        if not Notification.objects.filter(user=request.user).exists():
            Notification.objects.create(
                user=request.user,
                notification_type='general',
                message='Welcome to TAU Agrostudies Portal! Your application has been received and is under review.'
            )
    
    context = {
        'applicant': applicant,
        'farm_applications': farm_applications,
            'unread_notifications_count': Notification.objects.filter(user=request.user, read=False).count(),
    }
        print("DEBUG: Rendering dashboard template")
    return render(request, 'applicants/dashboard.html', context)
    except Applicant.DoesNotExist:
        print("DEBUG: Applicant does not exist, redirecting to register_applicant")
        messages.error(request, 'You need to complete your profile before accessing the dashboard.')
        return redirect('applicants:register_applicant')
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        messages.error(request, f'An error occurred: {str(e)}')
        # Redirect to register applicant instead to prevent redirect loops
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
    # Check if the applicant's status is approved
    try:
        applicant = request.user.applicant
        if applicant.status != 'approved':
            messages.warning(request, 'Your application needs to be approved before you can view and apply to farms.')
            return redirect('applicants:dashboard')
    except:
        messages.error(request, 'Please complete your applicant profile first.')
        return redirect('applicants:dashboard')
    
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
    
    # Get the current applicant's farm applications
    applied_farms = set(FarmApplication.objects.filter(applicant=applicant).values_list('farm_id', flat=True))
    
    # Add a flag to each farm indicating if the applicant has already applied
    for farm in farms:
        farm.already_applied = farm.id in applied_farms
    
    context = {
        'farms': farms,
        'locations': Farm.objects.values_list('location', flat=True).distinct(),
        'specializations': Farm.objects.values_list('specialization', flat=True).distinct(),
    }
    return render(request, 'applicants/view_farms.html', context)

@login_required
def farm_detail(request, farm_id):
    # Check if the applicant's status is approved
    try:
        applicant = request.user.applicant
        if applicant.status != 'approved':
            messages.warning(request, 'Your application needs to be approved before you can view and apply to farms.')
            return redirect('applicants:dashboard')
    except:
        messages.error(request, 'Please complete your applicant profile first.')
        return redirect('applicants:dashboard')
    
    farm = get_object_or_404(Farm, id=farm_id)
    already_applied = FarmApplication.objects.filter(applicant=applicant, farm=farm).exists()
    return render(request, 'applicants/farm_detail.html', {'farm': farm, 'already_applied': already_applied})

@login_required
def apply_to_farm(request, farm_id):
    # Check if the applicant's status is approved
    try:
        applicant = request.user.applicant
        if applicant.status != 'approved':
            messages.warning(request, 'Your application needs to be approved before you can apply to farms.')
            return redirect('applicants:dashboard')
    except:
        messages.error(request, 'Please complete your applicant profile first.')
        return redirect('applicants:dashboard')
    
    farm = get_object_or_404(Farm, id=farm_id)
    
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

    # Get all documents for the applicant
    documents = Document.objects.filter(applicant=applicant)
    
    # Create a dictionary of document types and their corresponding documents
    document_dict = {doc.document_type: doc for doc in documents}
    
    # Define required document types
    required_document_types = ['resume', 'transcript']
    
    # Define allowed file extensions for each document type
    allowed_extensions = {
        'resume': ['.pdf', '.doc', '.docx'],
        'transcript': ['.pdf'],
        'passport': ['.pdf', '.jpg', '.jpeg', '.png'],
        'medical_certificate': ['.pdf', '.jpg', '.jpeg', '.png'],
        'recommendation_letter': ['.pdf', '.doc', '.docx'],
        'other': ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    }
    
    # Define MIME types for each extension
    mime_types = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }

    if request.method == 'POST' and request.FILES:
        document_type = request.POST.get('document_type')
        
        if document_type in dict(Document.DOCUMENT_TYPES):
            file_field_name = document_type
            
            if file_field_name in request.FILES:
                file = request.FILES[file_field_name]
                file_extension = os.path.splitext(file.name)[1].lower()
                
                # Check if the file extension is allowed for this document type
                if file_extension not in allowed_extensions.get(document_type, []):
                    allowed_ext_list = ', '.join(allowed_extensions.get(document_type, []))
                    messages.error(request, f'{Document.DOCUMENT_TYPES_DICT.get(document_type)} must be one of these formats: {allowed_ext_list}')
                    return render(request, 'applicants/upload_documents.html', {
                        'documents': document_dict,
                        'required_document_types': required_document_types
                    })
                
                # Check if there's an existing document to replace
                is_replacement = document_type in document_dict
                
                # If there's an existing document, delete it
                if is_replacement:
                    document_dict[document_type].file.delete(save=False)
                    document_dict[document_type].delete()
                
                # Create a new document
                document = Document(
                    applicant=applicant,
                    document_type=document_type,
                    file=file,
                    original_filename=file.name,
                    file_size=file.size,
                    file_type=mime_types.get(file_extension, 'application/octet-stream'),
                    is_required=document_type in required_document_types
                )
                document.save()
                
                # Update the document dictionary
                document_dict[document_type] = document
                
                # Create a notification for the admin
                admin_users = User.objects.filter(is_staff=True)
                for admin in admin_users:
                    Notification.objects.create(
                        user=admin,
                        notification_type='document_reminder',
                        message=f"New document uploaded: {document.get_document_type_display()} by {applicant.full_name}"
                    )
                
                if is_replacement:
                    messages.success(request, f'{document.get_document_type_display()} replaced successfully!')
                else:
                    messages.success(request, f'{document.get_document_type_display()} uploaded successfully!')
            else:
                messages.error(request, f'Please select a {Document.DOCUMENT_TYPES_DICT.get(document_type)} file to upload.')
        else:
            messages.error(request, 'Invalid document type.')
    
    # For backward compatibility with the old system
    # Map old document fields to the new Document model
    if hasattr(applicant, 'resume') and applicant.resume and 'resume' not in document_dict:
        # Create a Document object for the resume
        try:
            resume_doc = Document(
                applicant=applicant,
                document_type='resume',
                file=applicant.resume,
                original_filename=os.path.basename(applicant.resume.name),
                file_size=applicant.resume.size,
                file_type='application/pdf',  # Assuming PDF for simplicity
                status=applicant.resume_status,
                verified_at=applicant.resume_verified_at,
                verified_by=applicant.resume_verified_by,
                verification_notes=applicant.resume_verification_notes,
                is_required=True
            )
            resume_doc.save()
            document_dict['resume'] = resume_doc
        except Exception as e:
            print(f"Error migrating resume: {str(e)}")
    
    if hasattr(applicant, 'transcript') and applicant.transcript and 'transcript' not in document_dict:
        # Create a Document object for the transcript
        try:
            transcript_doc = Document(
                applicant=applicant,
                document_type='transcript',
                file=applicant.transcript,
                original_filename=os.path.basename(applicant.transcript.name),
                file_size=applicant.transcript.size,
                file_type='application/pdf',  # Assuming PDF
                status=applicant.transcript_status,
                verified_at=applicant.transcript_verified_at,
                verified_by=applicant.transcript_verified_by,
                verification_notes=applicant.transcript_verification_notes,
                is_required=True
            )
            transcript_doc.save()
            document_dict['transcript'] = transcript_doc
        except Exception as e:
            print(f"Error migrating transcript: {str(e)}")
    
    return render(request, 'applicants/upload_documents.html', {
        'documents': document_dict,
        'required_document_types': required_document_types,
        'document_types': Document.DOCUMENT_TYPES
    })

@login_required
def update_profile(request):
    """View for updating user profile"""
    try:
        applicant = request.user.applicant
    except Applicant.DoesNotExist:
        messages.error(request, "You don't have an applicant profile.")
        return redirect('applicants:register_applicant')
    
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
        
        # Removed countries from context
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
    # Get all applicants
    applicants = Applicant.objects.all().order_by('-created_at')
    
    # Get all documents
    documents = Document.objects.all()
    
    # Filter by document status if requested
    document_type = request.GET.get('document_type')
    document_status = request.GET.get('document_status')
    
    if document_type:
        documents = documents.filter(document_type=document_type)
    if document_status:
        documents = documents.filter(status=document_status)
    
    # Group documents by applicant
    applicant_documents = {}
    for doc in documents:
        if doc.applicant_id not in applicant_documents:
            applicant_documents[doc.applicant_id] = []
        applicant_documents[doc.applicant_id].append(doc)
    
    # Filter applicants who have documents matching the filters
    if document_type or document_status:
        filtered_applicant_ids = list(applicant_documents.keys())
        applicants = applicants.filter(id__in=filtered_applicant_ids)
    
    context = {
        'applicants': applicants,
        'applicant_documents': applicant_documents,
        'document_types': Document.DOCUMENT_TYPES,
        'status_choices': Document.STATUS_CHOICES,
        'current_document_type': document_type,
        'current_document_status': document_status,
    }
    return render(request, 'applicants/view_all_documents.html', context)

@login_required
@user_passes_test(is_admin)
def verify_document(request, applicant_id):
    """View for admins to verify applicant documents"""
    applicant = get_object_or_404(Applicant, id=applicant_id)
    
    # Get all documents for the applicant
    documents = Document.objects.filter(applicant=applicant)
    
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if document_type and status:
            try:
                # Find the document by type
                document = Document.objects.get(applicant=applicant, document_type=document_type)
                
                # Update document status
                document.status = status
                document.verification_notes = notes
                document.verified_at = timezone.now()
                document.verified_by = request.user
                document.save()
                
                # Create a notification for the applicant
                status_display = dict(Document.STATUS_CHOICES).get(status, status)
                document_type_display = dict(Document.DOCUMENT_TYPES).get(document_type, document_type)
                
                Notification.objects.create(
                    user=applicant.user,
                    notification_type='application_status',
                    message=f"Your {document_type_display} has been {status_display}. {notes if notes else ''}"
                )
                
                messages.success(request, f'{document_type_display} status updated to {status_display}')
            except Document.DoesNotExist:
                messages.error(request, f'Document of type {document_type} not found for this applicant')
        else:
            messages.error(request, 'Missing document type or status')
    
    # For backward compatibility with the old system
    # Map old document fields to the new Document model
    if hasattr(applicant, 'resume') and applicant.resume and not documents.filter(document_type='resume').exists():
        # Create a Document object for the resume
        try:
            resume_doc = Document(
                applicant=applicant,
                document_type='resume',
                file=applicant.resume,
                original_filename=os.path.basename(applicant.resume.name),
                file_size=applicant.resume.size,
                file_type='application/pdf',  # Assuming PDF for simplicity
                status=applicant.resume_status,
                verified_at=applicant.resume_verified_at,
                verified_by=applicant.resume_verified_by,
                verification_notes=applicant.resume_verification_notes,
                is_required=True
            )
            resume_doc.save()
            documents = Document.objects.filter(applicant=applicant)  # Refresh documents
        except Exception as e:
            print(f"Error migrating resume: {str(e)}")
    
    if hasattr(applicant, 'transcript') and applicant.transcript and not documents.filter(document_type='transcript').exists():
        # Create a Document object for the transcript
        try:
            transcript_doc = Document(
                applicant=applicant,
                document_type='transcript',
                file=applicant.transcript,
                original_filename=os.path.basename(applicant.transcript.name),
                file_size=applicant.transcript.size,
                file_type='application/pdf',  # Assuming PDF
                status=applicant.transcript_status,
                verified_at=applicant.transcript_verified_at,
                verified_by=applicant.transcript_verified_by,
                verification_notes=applicant.transcript_verification_notes,
                is_required=True
            )
            transcript_doc.save()
            documents = Document.objects.filter(applicant=applicant)  # Refresh documents
        except Exception as e:
            print(f"Error migrating transcript: {str(e)}")
    
    # Organize documents by type for the template
    document_dict = {doc.document_type: doc for doc in documents}
    
    context = {
        'applicant': applicant,
        'documents': document_dict,
        'document_types': Document.DOCUMENT_TYPES,
        'status_choices': Document.STATUS_CHOICES,
    }
    return render(request, 'applicants/verify_document.html', context)

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

@login_required
@user_passes_test(is_admin)
def send_document_reminder(request, applicant_id):
    """View for admins to send document reminders to applicants"""
    applicant = get_object_or_404(Applicant, id=applicant_id)
    
    if request.method == 'POST':
        document_types = request.POST.getlist('document_types')
        custom_message = request.POST.get('custom_message', '')
        
        # Create a message based on the selected document types
        if document_types:
            # Get the display names for the selected document types
            document_type_names = [dict(Document.DOCUMENT_TYPES).get(doc_type, doc_type) for doc_type in document_types]
            
            # Format the list of document types
            if len(document_type_names) == 1:
                document_list = document_type_names[0]
            elif len(document_type_names) == 2:
                document_list = f"{document_type_names[0]} and {document_type_names[1]}"
            else:
                document_list = ", ".join(document_type_names[:-1]) + f", and {document_type_names[-1]}"
            
            # Create the base message
            base_message = f"Please upload your {document_list} as soon as possible for your application to proceed."
            
            # Add custom message if provided
            if custom_message:
                notification_message = f"{base_message} {custom_message}"
            else:
                notification_message = base_message
            
            # Create a notification in the system
            Notification.objects.create(
                user=applicant.user,
                notification_type='document_reminder',
                message=notification_message
            )
            
            messages.success(request, f"Reminder sent to {applicant.full_name} about uploading {document_list}.")
        else:
            messages.error(request, "Please select at least one document type.")
        
        return redirect('applicants:verify_document', applicant_id=applicant_id)
    
    # If it's a GET request, redirect back to the verify document page
    return redirect('applicants:verify_document', applicant_id=applicant_id)

# Privacy Policy and Terms of Service views have been removed as they are now implemented as modals in the base template

@login_required
def get_notifications(request):
    """Get all notifications for the current user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return JsonResponse({
        'notifications': list(notifications.values('id', 'message', 'created_at', 'is_read', 'notification_type')),
        'unread_count': notifications.filter(is_read=False).count()
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
@user_passes_test(is_admin)
def send_notification(request, applicant_id):
    """Send a notification to an applicant"""
    applicant = get_object_or_404(Applicant, id=applicant_id)
    
    if request.method == 'POST':
        notification_type = request.POST.get('notification_type', 'general')
        message = request.POST.get('message', '')
        
        if message:
            Notification.objects.create(
                user=applicant.user,
                notification_type=notification_type,
                message=message
            )
            messages.success(request, f'Notification sent to {applicant.full_name}')
        else:
            messages.error(request, 'Please provide a message for the notification')
        
        # Redirect back to the referring page
        return redirect(request.META.get('HTTP_REFERER', 'applicants:applicant_list'))
    
    # If not POST, redirect to applicant list
    return redirect('applicants:applicant_list')

