from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Custom permission to allow only admin users to access certain views.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff  # Only allow admins
