from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in with their email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find a user matching the username or email
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
            # Check the password
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # No user was found with the provided username/email
            return None
        except User.MultipleObjectsReturned:
            # More than one user has this email (should be prevented by validation)
            # Return the first one that matches
            user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            if user.check_password(password):
                return user
        return None 