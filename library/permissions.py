from rest_framework import permissions

class IsLibrarianOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow librarians to edit objects. Regular users can only read."""
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to librarians
        return (request.user and request.user.is_authenticated and request.user.is_librarian)
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to librarians
        return (request.user and request.user.is_authenticated and request.user.is_librarian)

class IsOwnerOrLibrarian(permissions.BasePermission):
    """Custom permission to only allow owners of an object or librarians to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to the owner or librarians
        return (request.user and request.user.is_authenticated and 
                (obj.user == request.user or request.user.is_librarian))