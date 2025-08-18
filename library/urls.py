from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import authentication

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', authentication.register, name='register'),
    path('auth/login/', authentication.login, name='login'),
    path('auth/logout/', authentication.logout, name='logout'),
    path('auth/refresh/', authentication.refresh_token, name='token_refresh'),
    
    # User profile
    path('auth/profile/', views.user_profile, name='user_profile'),
    
    # Dashboard and statistics
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('books/popular/', views.popular_books, name='popular_books'),
    path('books/recent/', views.recent_books, name='recent_books'),
    
    # Categories
    path('categories/', views.CategoryListCreateView.as_view(), name='category_list_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Books
    path('books/', views.BookListCreateView.as_view(), name='book_list_create'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('books/search/', views.BookSearchView.as_view(), name='book_search'),
    
    # Borrowings
    path('borrowings/', views.UserBorrowingsView.as_view(), name='user_borrowings'),
    path('borrowings/all/', views.AllBorrowingsView.as_view(), name='all_borrowings'),
    path('borrowings/borrow/', views.borrow_book, name='borrow_book'),
    path('borrowings/return/', views.return_book, name='return_book'),
]