from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    """API root endpoint with available endpoints"""
    return JsonResponse({
        'message': 'Welcome to Book Library API',
        'version': '1.0.0',
        'endpoints': {
            'authentication': {
                'register': '/api/auth/register/',
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'refresh': '/api/auth/refresh/',
                'profile': '/api/auth/profile/',
            },
            'books': {
                'list_create': '/api/books/',
                'detail': '/api/books/{id}/',
                'search': '/api/books/search/',
                'popular': '/api/books/popular/',
                'recent': '/api/books/recent/',
            },
            'categories': {
                'list_create': '/api/categories/',
                'detail': '/api/categories/{id}/',
            },
            'borrowings': {
                'user_borrowings': '/api/borrowings/',
                'all_borrowings': '/api/borrowings/all/',
                'borrow': '/api/borrowings/borrow/',
                'return': '/api/borrowings/return/',
            },
            'dashboard': {
                'stats': '/api/dashboard/stats/',
            }
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('library.urls')),
    path('', api_root, name='api_root'),
]