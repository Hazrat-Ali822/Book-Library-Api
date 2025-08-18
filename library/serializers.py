from rest_framework import serializers
from .models import User, Category, Book, Borrowing
from django.utils import timezone
from datetime import timedelta

class UserSerializer(serializers.ModelSerializer):
    """User serializer for API responses"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_librarian', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    books_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'books_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_books_count(self, obj):
        return obj.books.count()

class BookSerializer(serializers.ModelSerializer):
    """Book serializer"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'isbn', 'publication_date', 'category', 
            'category_name', 'description', 'total_copies', 'available_copies',
            'is_available', 'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def validate(self, data):
        """Validate book data"""
        if 'available_copies' in data and 'total_copies' in data:
            if data['available_copies'] > data['total_copies']:
                raise serializers.ValidationError("Available copies cannot exceed total copies")
        return data

class BookCreateUpdateSerializer(serializers.ModelSerializer):
    """Book serializer for create and update operations (admin only)"""
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'publication_date', 'category',
            'description', 'total_copies', 'available_copies'
        ]
    
    def validate(self, data):
        """Validate book data"""
        if 'available_copies' in data and 'total_copies' in data:
            if data['available_copies'] > data['total_copies']:
                raise serializers.ValidationError("Available copies cannot exceed total copies")
        return data

class BorrowingSerializer(serializers.ModelSerializer):
    """Borrowing serializer"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Borrowing
        fields = [
            'id', 'user', 'user_name', 'user_email', 'book', 'book_title', 
            'book_author', 'borrowed_date', 'due_date', 'returned_date', 
            'status', 'notes', 'is_overdue'
        ]
        read_only_fields = ['id', 'borrowed_date', 'user']

class BorrowBookSerializer(serializers.Serializer):
    """Serializer for borrowing a book"""
    book_id = serializers.IntegerField()
    due_date = serializers.DateField(required=False)
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_book_id(self, value):
        """Validate that book exists and is available"""
        try:
            book = Book.objects.get(id=value)
            if not book.is_available():
                raise serializers.ValidationError("Book is not available for borrowing")
            return value
        except Book.DoesNotExist:
            raise serializers.ValidationError("Book does not exist")
    
    def validate_due_date(self, value):
        """Validate due date is in the future"""
        if value and value <= timezone.now().date():
            raise serializers.ValidationError("Due date must be in the future")
        return value
    
    def create(self, validated_data):
        """Create a new borrowing record"""
        user = self.context['request'].user
        book = Book.objects.get(id=validated_data['book_id'])
        
        # Set default due date if not provided (14 days from now)
        due_date = validated_data.get('due_date')
        if not due_date:
            due_date = timezone.now().date() + timedelta(days=14)
        
        # Create borrowing record
        borrowing = Borrowing.objects.create(
            user=user,
            book=book,
            due_date=due_date,
            notes=validated_data.get('notes', '')
        )
        
        # Update book availability
        book.available_copies -= 1
        book.save()
        
        return borrowing

class ReturnBookSerializer(serializers.Serializer):
    """Serializer for returning a book"""
    borrowing_id = serializers.IntegerField()
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_borrowing_id(self, value):
        """Validate that borrowing exists and belongs to the user"""
        user = self.context['request'].user
        try:
            borrowing = Borrowing.objects.get(id=value, user=user)
            if borrowing.status == 'returned':
                raise serializers.ValidationError("Book has already been returned")
            return value
        except Borrowing.DoesNotExist:
            raise serializers.ValidationError("Borrowing record does not exist or does not belong to you")
    
    def update(self, instance, validated_data):
        """Update borrowing record to mark as returned"""
        borrowing = Borrowing.objects.get(id=validated_data['borrowing_id'])
        
        # Update borrowing record
        borrowing.returned_date = timezone.now()
        borrowing.status = 'returned'
        if 'notes' in validated_data:
            borrowing.notes = validated_data['notes']
        borrowing.save()
        
        # Update book availability
        book = borrowing.book
        book.available_copies += 1
        book.save()
        
        return borrowing