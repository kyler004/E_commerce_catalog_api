from django.urls import path

from wishlists.views import (
    WishlistDetailView,
    WishlistItemCreateView,
    WishlistItemDetailView,
    WishlistMoveToCartView,
)

urlpatterns = [
    path('', WishlistDetailView.as_view(), name='wishlist-detail'),
    path('items/', WishlistItemCreateView.as_view(), name='wishlist-item-create'),
    path('items/<int:item_id>/', WishlistItemDetailView.as_view(), name='wishlist-item-detail'),
    path(
        'items/<int:item_id>/move-to-cart/',
        WishlistMoveToCartView.as_view(),
        name='wishlist-move-to-cart',
    ),
]
