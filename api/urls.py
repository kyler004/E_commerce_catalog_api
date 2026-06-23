from django.urls import path, include
from rest_framework.routers import DefaultRouter
from reviews.views import ProductReviewListCreateView, ReviewDetailView
from .views import CategoryViewSet, ProductViewSet, VariantViewSet, InventoryViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'variants', VariantViewSet)
router.register(r'inventories', InventoryViewSet)

urlpatterns = [
    path('products/<int:product_id>/reviews/', ProductReviewListCreateView.as_view(), name='product-reviews'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('', include(router.urls)),
]