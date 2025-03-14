from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'applicants'

urlpatterns = [
    # Core pages
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='applicants:landing'), name='logout'),
    path('register/select/', views.role_selection, name='register'),
    path('register/applicant/', views.register_applicant, name='register_applicant'),
    path('register/admin/', views.register_admin, name='register_admin'),

    # Farm Management
    path('farms/', views.view_farms, name='view_farms'),
    path('farm/<int:farm_id>/', views.farm_detail, name='farm_detail'),
    path('farm/<int:farm_id>/apply/', views.apply_to_farm, name='apply_to_farm'),
    path('manage-farm-applications/', views.manage_farm_applications, name='manage_farm_applications'),
    path('update-farm-application/<int:application_id>/', views.update_farm_application, name='update_farm_application'),

    # Applicant Management
    path('applicants/', views.applicant_list, name='applicant_list'),
    path('review-applications/', views.review_applications_list, name='review_applications_list'),
    path('review/<str:student_number>/', views.review_application, name='review_application'),
    
    # Admin Features
    path('reports/', views.generate_reports, name='generate_reports'),
    path('documents/view-all/', views.view_all_documents, name='view_all_documents'),
    path('documents/verify/<int:applicant_id>/', views.verify_document, name='verify_document'),
    
    # User Features
    path('documents/upload/', views.upload_documents, name='upload_documents'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('support/', views.contact_support, name='contact_support'),
    
    # This must be last as it's a catch-all pattern
    path('<str:student_number>/', views.applicant_detail, name='applicant_detail'),
    path('delete/<str:student_number>/', views.delete_applicant, name='delete_applicant'),
]
