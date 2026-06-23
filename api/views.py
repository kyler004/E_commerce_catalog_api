from django.db.models import Avg, Count
from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.permissions import IsEmailVerified
from .models import Category, Product, Variant, Inventory
from .serializers import CategorySerializer, ProductSerializer, VariantSerializer, InventorySerializer
from .filters import ProductFilter

class StandardPagination(PageNumberPagination):
    page_size = 10  # Default items per page
    page_size_query_param = 'page_size'
    max_page_size = 100


class CatalogWritePermissionMixin:
    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated(), IsEmailVerified()]


class CategoryViewSet(CatalogWritePermissionMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'parent']  # Filter by exact name or parent
    search_fields = ['name', 'description']  # Search in these fields
    ordering_fields = ['name', 'created_at']  # Allow ordering

class ProductViewSet(CatalogWritePermissionMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    def get_queryset(self):
        return Product.objects.annotate(
            average_rating=Avg('reviews__rating'),
            review_count=Count('reviews'),
        ).prefetch_related('variants__inventory')

# Similarly for Variant and Inventory
class VariantViewSet(CatalogWritePermissionMixin, viewsets.ModelViewSet):
    queryset = Variant.objects.all()
    serializer_class = VariantSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['product', 'size', 'color']
    search_fields = ['sku']

class InventoryViewSet(CatalogWritePermissionMixin, viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['variant', 'quantity']