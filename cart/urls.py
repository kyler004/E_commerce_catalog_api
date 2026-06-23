from django.urls import path

from cart.views import (
    CartApplyPromoView,
    CartDetailView,
    CartItemCreateView,
    CartItemDetailView,
    CartRemovePromoView,
)

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart-detail'),
    path('apply-promo/', CartApplyPromoView.as_view(), name='cart-apply-promo'),
    path('promo/', CartRemovePromoView.as_view(), name='cart-remove-promo'),
    path('items/', CartItemCreateView.as_view(), name='cart-item-create'),
    path('items/<int:item_id>/', CartItemDetailView.as_view(), name='cart-item-detail'),
]
