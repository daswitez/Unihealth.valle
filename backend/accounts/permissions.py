from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Permite solo a rol 'admin'.
    """

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "role", "") == "admin")


class IsNurse(BasePermission):
    """
    Permite solo a rol 'nurse'.
    """

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "role", "") == "nurse")


class IsUser(BasePermission):
    """
    Permite solo a rol 'user'.
    """

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "role", "") == "user")

