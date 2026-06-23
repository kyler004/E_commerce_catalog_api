from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsEmailVerified
from cart.models import CartItem
from cart.serializers import (
    CartItemAddSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartSerializer,
)
from cart.services import (
    CartValidationError,
    add_item,
    clear_cart,
    compute_cart_summary,
    get_or_create_cart,
    remove_item,
    update_item,
)


class CartPermissionMixin:
    permission_classes = [IsAuthenticated, IsEmailVerified]


def _serialize_cart(cart):
    items = cart.items.select_related('variant__product', 'variant__inventory')
    summary = compute_cart_summary(cart)
    return CartSerializer({
        'id': cart.id,
        'items': items,
        'item_count': summary['item_count'],
        'subtotal': summary['subtotal'],
        'updated_at': cart.updated_at,
    }).data


class CartDetailView(CartPermissionMixin, APIView):
    def get(self, request):
        cart = get_or_create_cart(request.user)
        return Response(_serialize_cart(cart))

    def delete(self, request):
        clear_cart(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemCreateView(CartPermissionMixin, APIView):
    def post(self, request):
        serializer = CartItemAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item, _created = add_item(
                request.user,
                serializer.validated_data['variant'],
                serializer.validated_data['quantity'],
            )
        except CartValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        item = CartItem.objects.select_related(
            'variant__product', 'variant__inventory'
        ).get(pk=item.pk)
        cart = get_or_create_cart(request.user)
        data = CartItemSerializer(item).data
        data['cart'] = _serialize_cart(cart)
        return Response(data, status=status.HTTP_201_CREATED)


class CartItemDetailView(CartPermissionMixin, APIView):
    def patch(self, request, item_id):
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = update_item(
                request.user,
                item_id,
                serializer.validated_data['quantity'],
            )
        except CartItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except CartValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        item = CartItem.objects.select_related(
            'variant__product', 'variant__inventory'
        ).get(pk=item.pk)
        cart = get_or_create_cart(request.user)
        data = CartItemSerializer(item).data
        data['cart'] = _serialize_cart(cart)
        return Response(data)

    def delete(self, request, item_id):
        try:
            remove_item(request.user, item_id)
        except CartItem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
