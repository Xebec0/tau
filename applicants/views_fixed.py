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
