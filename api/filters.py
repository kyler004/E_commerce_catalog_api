import django_filters
from .models import Product

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    color = django_filters.CharFilter(field_name="variants__color", lookup_expr='icontains')
    size = django_filters.CharFilter(field_name="variants__size", lookup_expr='icontains')
    category = django_filters.NumberFilter(field_name="category")

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'color', 'size', 'category']
