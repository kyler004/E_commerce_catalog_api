from django.urls import path

from orders.views import (
    CancelOrderView,
    CheckoutView,
    ConfirmPaymentView,
    OrderDetailView,
    OrderListView,
    OrderReceiptView,
)

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='order-checkout'),
    path('', OrderListView.as_view(), name='order-list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:order_id>/confirm-payment/', ConfirmPaymentView.as_view(), name='order-confirm-payment'),
    path('<int:order_id>/cancel/', CancelOrderView.as_view(), name='order-cancel'),
    path('<int:order_id>/receipt/', OrderReceiptView.as_view(), name='order-receipt'),
]
