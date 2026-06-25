from django.http import HttpResponse
from django.template.loader import render_to_string
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
    OrderListQuerySerializer,
    OrderSerializer,
    SpendingSummaryQuerySerializer,
)
from orders.services import (
    OrderNotFoundError,
    OrderStateError,
    OrderValidationError,
    cancel_order,
    checkout,
    confirm_payment,
    filter_user_orders,
    get_receipt_order,
    get_spending_summary,
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
        query_serializer = OrderListQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        return filter_user_orders(self.request.user, query_serializer.validated_data)


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


class OrderReceiptView(OrderPermissionMixin, APIView):
    def get(self, request, order_id):
        try:
            order = get_receipt_order(request.user, order_id)
        except OrderNotFoundError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except OrderStateError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        html = render_to_string('orders/receipt.html', {'order': order})
        return HttpResponse(html, content_type='text/html')


class SpendingSummaryView(OrderPermissionMixin, APIView):
    def get(self, request):
        serializer = SpendingSummaryQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(
            get_spending_summary(
                request.user,
                period=serializer.validated_data['period'],
            )
        )
