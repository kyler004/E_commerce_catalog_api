from rest_framework.permissions import BasePermission


class IsEmailVerified(BasePermission):
    message = 'Email address is not verified.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.email_verified_at is not None
        )


class IsStaff(BasePermission):
    message = 'Staff access required.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff
