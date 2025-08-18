from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_librarian = models.BooleanField(default=False, help_text="Designates whether the user can manage books.")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class Category(models.Model):
    """Book categories for filtering"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Book(models.Model):
    """Book model with all necessary fields"""
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True, help_text="13-digit ISBN")
    publication_date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books')
    description = models.TextField(blank=True)
    total_copies = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    available_copies = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_books')
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    def is_available(self):
        """Check if book is available for borrowing"""
        return self.available_copies > 0
    
    def save(self, *args, **kwargs):
        """Ensure available_copies doesn't exceed total_copies"""
        if self.available_copies > self.total_copies:
            self.available_copies = self.total_copies
        super().save(*args, **kwargs)

class Borrowing(models.Model):
    """Borrowing records for tracking book loans"""
    BORROWING_STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrowings')
    borrowed_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=BORROWING_STATUS_CHOICES, default='borrowed')
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-borrowed_date']
        unique_together = ['user', 'book', 'borrowed_date']
    
    def __str__(self):
        return f"{self.user.username} borrowed {self.book.title}"
    
    @property
    def is_overdue(self):
        """Check if the borrowing is overdue"""
        from django.utils import timezone
        if self.status == 'returned':
            return False
        return timezone.now().date() > self.due_date
    
    def save(self, *args, **kwargs):
        """Update status based on due date"""
        if self.is_overdue and self.status == 'borrowed':
            self.status = 'overdue'
        super().save(*args, **kwargs)