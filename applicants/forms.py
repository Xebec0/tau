from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import Applicant, FarmApplication
import re
from datetime import date, timedelta

class ApplicantRegistrationForm(UserCreationForm):
    COUNTRIES = [
        ('Philippines', 'Philippines'),
        ('Japan', 'Japan'),
        ('South Korea', 'South Korea'),
        ('Israel', 'Israel'),
        ('Thailand', 'Thailand'),
        ('Vietnam', 'Vietnam'),
        ('Indonesia', 'Indonesia'),
        ('Malaysia', 'Malaysia'),
        ('Singapore', 'Singapore'),
        ('China', 'China'),
    ]

    first_name = forms.CharField(
        max_length=50,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z\s]+$', 
                message="First name must contain only letters and spaces"
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter first name',
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )

    middle_name = forms.CharField(
        max_length=50,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z\s]*$', 
                message="Middle name must contain only letters and spaces"
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter middle name (optional)',
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )

    last_name = forms.CharField(
        max_length=50,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z\s]+$', 
                message="Last name must contain only letters and spaces"
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter last name',
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )

    student_number = forms.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9]{6,10}$',
                message="Student number must be 6-10 uppercase letters or numbers"
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter student number',
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )

    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        }),
        required=True
    )

    gender = forms.ChoiceField(
        choices=Applicant.GENDER_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        required=True
    )

    phone_number = forms.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be a valid international format"
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter phone number',
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password1', 'password2',
            'first_name', 'middle_name', 'last_name', 'student_number', 'date_of_birth',
            'gender', 'phone_number'
        ]

    def clean_username(self):
        username = self.cleaned_data['username']
        if len(username) < 4 or len(username) > 20:
            raise ValidationError("Username must be between 4 and 20 characters.")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use.")
        return email

    def clean_student_number(self):
        student_number = self.cleaned_data['student_number']
        if Applicant.objects.filter(student_number=student_number).exists():
            raise ValidationError("This student number is already registered.")
        return student_number

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            min_age_date = today - timedelta(days=16*365)
            max_age_date = today - timedelta(days=100*365)
            
            # Calculate age
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if dob > min_age_date:
                raise ValidationError("You must be at least 16 years old to register.")
            if dob < max_age_date:
                raise ValidationError("Your age seems unrealistic.")
            if age >= 30:
                raise ValidationError("We're sorry, but applicants must be under 30 years old to apply. You are not eligible for this program.")
        return dob

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password1):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password1):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'\d', password1):
            raise ValidationError("Password must contain at least one number.")
        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Create associated Applicant profile
            Applicant.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                middle_name=self.cleaned_data['middle_name'],
                last_name=self.cleaned_data['last_name'],
                student_number=self.cleaned_data['student_number'],
                date_of_birth=self.cleaned_data['date_of_birth'],
                gender=self.cleaned_data['gender'],
                phone_number=self.cleaned_data['phone_number']
            )
        return user


class AdminRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=100)
    phone_number = forms.CharField(
        max_length=20, 
        widget=forms.TextInput(attrs={'placeholder': 'Enter phone number'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'full_name', 'phone_number']

    def clean_email(self):
        # Validate email uniqueness
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_phone_number(self):
        # Optional: Add phone number validation
        phone_number = self.cleaned_data['phone_number']
        # Example: Basic phone number validation
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Set additional user attributes
        user.email = self.cleaned_data['email']
        user.is_staff = True
        user.is_superuser = True  # Give full admin privileges
        
        # Optional: You might want to create a profile or admin-specific model
        # that stores additional information like full_name and phone_number
        
        if commit:
            user.save()
            # Optionally create an admin profile
            # AdminProfile.objects.create(
            #     user=user,
            #     full_name=self.cleaned_data['full_name'],
            #     phone_number=self.cleaned_data['phone_number']
            # )
        
        return user

class FarmApplicationUpdateForm(forms.ModelForm):
    class Meta:
        model = FarmApplication
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""
    first_name = forms.CharField(
        max_length=50,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z\s]+$', 
                message="First name must contain only letters and spaces"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )

    middle_name = forms.CharField(
        max_length=50,
        required=False,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z\s]*$', 
                message="Middle name must contain only letters and spaces"
            )
        ],
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter middle name (optional)',
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )

    last_name = forms.CharField(
        max_length=50,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z\s]+$', 
                message="Last name must contain only letters and spaces"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be a valid international format"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]'
        })
    )
    
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]',
            'accept': 'image/*'
        })
    )
    
    # Social media fields
    linkedin_profile = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]',
            'placeholder': 'https://linkedin.com/in/yourprofile'
        })
    )
    
    facebook_profile = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]',
            'placeholder': 'https://facebook.com/yourprofile'
        })
    )
    
    twitter_profile = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]',
            'placeholder': 'https://twitter.com/yourhandle'
        })
    )
    
    instagram_profile = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'p-2 border rounded w-full focus:ring-2 focus:ring-[#795548]',
            'placeholder': 'https://instagram.com/yourhandle'
        })
    )
    
    class Meta:
        model = Applicant
        fields = [
            'first_name', 'middle_name', 'last_name', 'phone_number', 'profile_photo',
            'linkedin_profile', 'facebook_profile', 'twitter_profile', 'instagram_profile'
        ]
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.initial['email'] = user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_id = self.instance.user.id
        if User.objects.exclude(id=user_id).filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
