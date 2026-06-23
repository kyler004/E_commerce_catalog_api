from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsEmailVerified
from api.views import StandardPagination
from orders.serializers import (
    CheckoutSerializer,
    OrderListSerializer,
    OrderSerializer,
)
from orders.services import (
    OrderNotFoundError,
    OrderStateError,
    OrderValidationError,
    cancel_order,
    checkout,
    confirm_payment,
    get_user_order,
    get_user_orders,
)


class OrderPermissionMixin:
    permission_classes = [IsAuthenticated, IsEmailVerified]


class CheckoutView(OrderPermissionMixin, APIView):
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = checkout(request.user, serializer.validated_data['shipping'])
        except OrderValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderListView(OrderPermissionMixin, ListAPIView):
    serializer_class = OrderListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return get_user_orders(self.request.user)


class OrderDetailView(OrderPermissionMixin, RetrieveAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return get_user_orders(self.request.user)


class ConfirmPaymentView(OrderPermissionMixin, APIView):
    def post(self, request, order_id):
        try:
            order = confirm_payment(request.user, order_id)
        except OrderNotFoundError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except OrderStateError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except OrderValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(OrderSerializer(order).data)


class CancelOrderView(OrderPermissionMixin, APIView):
    def post(self, request, order_id):
        try:
            order = cancel_order(request.user, order_id)
        except OrderNotFoundError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except OrderStateError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(OrderSerializer(order).data)
