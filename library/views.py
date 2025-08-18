from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import User, Category, Book, Borrowing
from .serializers import (
    UserSerializer, CategorySerializer, BookSerializer, BookCreateUpdateSerializer,
    BorrowingSerializer, BorrowBookSerializer, ReturnBookSerializer
)
from .permissions import IsLibrarianOrReadOnly

class CategoryListCreateView(generics.ListCreateAPIView):
    """List all categories or create a new category (librarian only for creation)"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsLibrarianOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a category (librarian only for update/delete)"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsLibrarianOrReadOnly]

class BookListCreateView(generics.ListCreateAPIView):
    """List all books with filtering or create a new book (librarian only for creation)"""
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticated, IsLibrarianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author']
    search_fields = ['title', 'author', 'isbn', 'description']
    ordering_fields = ['title', 'author', 'publication_date', 'created_at']
    ordering = ['title']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookCreateUpdateSerializer
        return BookSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class BookDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a book (librarian only for update/delete)"""
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticated, IsLibrarianOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BookCreateUpdateSerializer
        return BookSerializer

class BookSearchView(generics.ListAPIView):
    """Advanced book search with multiple filters"""
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author', 'isbn', 'description']
    ordering_fields = ['title', 'author', 'publication_date']
    ordering = ['title']
    
    def get_queryset(self):
        queryset = Book.objects.all()
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        
        # Filter by availability
        available_only = self.request.query_params.get('available_only', None)
        if available_only and available_only.lower() == 'true':
            queryset = queryset.filter(available_copies__gt=0)
        
        # Filter by author
        author = self.request.query_params.get('author', None)
        if author:
            queryset = queryset.filter(author__icontains=author)
        
        # Filter by publication year
        year = self.request.query_params.get('year', None)
        if year:
            queryset = queryset.filter(publication_date__year=year)
        
        return queryset

class UserBorrowingsView(generics.ListAPIView):
    """List current user's borrowings"""
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['borrowed_date', 'due_date', 'status']
    ordering = ['-borrowed_date']
    
    def get_queryset(self):
        return Borrowing.objects.filter(user=self.request.user)

class AllBorrowingsView(generics.ListAPIView):
    """List all borrowings (librarian only)"""
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated, IsLibrarianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'user', 'book']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'book__title', 'book__author']
    ordering_fields = ['borrowed_date', 'due_date', 'returned_date']
    ordering = ['-borrowed_date']

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def borrow_book(request):
    """Borrow a book"""
    serializer = BorrowBookSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        # Check if user already has this book borrowed
        book_id = serializer.validated_data['book_id']
        existing_borrowing = Borrowing.objects.filter(
            user=request.user,
            book_id=book_id,
            status__in=['borrowed', 'overdue']
        ).exists()
        
        if existing_borrowing:
            return Response({'error': 'You already have this book borrowed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check borrowing limit (max 5 books per user)
        active_borrowings = Borrowing.objects.filter(
            user=request.user,
            status__in=['borrowed', 'overdue']
        ).count()
        
        if active_borrowings >= 5:
            return Response({'error': 'You have reached the maximum borrowing limit (5 books)'}, status=status.HTTP_400_BAD_REQUEST)
        
        borrowing = serializer.save()
        return Response(BorrowingSerializer(borrowing).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def return_book(request):
    """Return a borrowed book"""
    serializer = ReturnBookSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        borrowing = serializer.save(instance=None)
        return Response({
            'message': 'Book returned successfully',
            'borrowing': BorrowingSerializer(borrowing).data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get current user's profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    if request.user.is_librarian:
        # Librarian dashboard
        stats = {
            'total_books': Book.objects.count(),
            'total_users': User.objects.filter(is_active=True).count(),
            'total_borrowings': Borrowing.objects.count(),
            'active_borrowings': Borrowing.objects.filter(status__in=['borrowed', 'overdue']).count(),
            'overdue_borrowings': Borrowing.objects.filter(status='overdue').count(),
            'available_books': Book.objects.filter(available_copies__gt=0).count(),
        }
    else:
        # Regular user dashboard
        user_borrowings = Borrowing.objects.filter(user=request.user)
        stats = {
            'total_borrowed': user_borrowings.count(),
            'currently_borrowed': user_borrowings.filter(status__in=['borrowed', 'overdue']).count(),
            'overdue_books': user_borrowings.filter(status='overdue').count(),
            'returned_books': user_borrowings.filter(status='returned').count(),
        }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def popular_books(request):
    """Get most popular books (most borrowed)"""
    from django.db.models import Count
    
    popular_books = Book.objects.annotate(
        borrow_count=Count('borrowings')
    ).order_by('-borrow_count')[:10]
    
    serializer = BookSerializer(popular_books, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_books(request):
    """Get recently added books"""
    recent_books = Book.objects.order_by('-created_at')[:10]
    serializer = BookSerializer(recent_books, many=True)
    return Response(serializer.data)