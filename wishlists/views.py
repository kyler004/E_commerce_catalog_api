from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsEmailVerified
from cart.serializers import CartItemSerializer
from wishlists.models import WishlistItem
from wishlists.serializers import (
    WishlistItemAddSerializer,
    WishlistItemSerializer,
    WishlistMoveToCartSerializer,
    WishlistSerializer,
)
from wishlists.services import (
    WishlistValidationError,
    add_product,
    get_or_create_wishlist,
    move_to_cart,
    remove_item,
)


class WishlistPermissionMixin:
    permission_classes = [IsAuthenticated, IsEmailVerified]


def _serialize_wishlist(wishlist):
    items = wishlist.items.select_related('product')
    return WishlistSerializer({
        'id': wishlist.id,
        'items': items,
        'item_count': items.count(),
        'updated_at': wishlist.updated_at,
    }).data


class WishlistDetailView(WishlistPermissionMixin, APIView):
    def get(self, request):
        wishlist = get_or_create_wishlist(request.user)
        return Response(_serialize_wishlist(wishlist))


class WishlistItemCreateView(WishlistPermissionMixin, APIView):
    def post(self, request):
        serializer = WishlistItemAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = add_product(request.user, serializer.validated_data['product'])
        except WishlistValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        item = WishlistItem.objects.select_related('product').get(pk=item.pk)
        return Response(WishlistItemSerializer(item).data, status=status.HTTP_201_CREATED)


class WishlistItemDetailView(WishlistPermissionMixin, APIView):
    def delete(self, request, item_id):
        try:
            remove_item(request.user, item_id)
        except WishlistItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistMoveToCartView(WishlistPermissionMixin, APIView):
    def post(self, request, item_id):
        serializer = WishlistMoveToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cart_item = move_to_cart(
                request.user,
                item_id,
                serializer.validated_data['variant'],
                serializer.validated_data['quantity'],
            )
        except WishlistItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except WishlistValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        from cart.views import _serialize_cart
        from cart.services import get_or_create_cart

        cart_item = type(cart_item).objects.select_related(
            'variant__product', 'variant__inventory'
        ).get(pk=cart_item.pk)
        data = CartItemSerializer(cart_item).data
        data['cart'] = _serialize_cart(get_or_create_cart(request.user))
        return Response(data, status=status.HTTP_201_CREATED)
