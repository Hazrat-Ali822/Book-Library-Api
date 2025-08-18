from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Book, Borrowing

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User admin configuration"""
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_librarian', 'is_staff', 'is_active')
    list_filter = ('is_librarian', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Library Permissions', {'fields': ('is_librarian',)}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Library Permissions', {'fields': ('is_librarian',)}),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin configuration"""
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Book admin configuration"""
    list_display = ('title', 'author', 'isbn', 'category', 'total_copies', 'available_copies', 'is_available')
    list_filter = ('category', 'publication_date', 'created_at')
    search_fields = ('title', 'author', 'isbn')
    ordering = ('title',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Book Information', {
            'fields': ('title', 'author', 'isbn', 'publication_date', 'category', 'description')
        }),
        ('Inventory', {
            'fields': ('total_copies', 'available_copies')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user if creating new book"""
        if not change:  # If creating new book
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    """Borrowing admin configuration"""
    list_display = ('user', 'book', 'borrowed_date', 'due_date', 'returned_date', 'status', 'is_overdue')
    list_filter = ('status', 'borrowed_date', 'due_date', 'returned_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'book__title', 'book__author')
    ordering = ('-borrowed_date',)
    readonly_fields = ('borrowed_date', 'is_overdue')
    
    fieldsets = (
        ('Borrowing Information', {
            'fields': ('user', 'book', 'borrowed_date', 'due_date', 'returned_date', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_overdue'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue(self, obj):
        """Display overdue status in admin"""
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'