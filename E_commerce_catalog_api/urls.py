"""
URL configuration for E_commerce_catalog_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from orders.views import SpendingSummaryView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/account/spending-summary/', SpendingSummaryView.as_view(), name='account-spending-summary'),
    path('api/auth/', include('accounts.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/wishlist/', include('wishlists.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/promotions/', include('promotions.urls')),
    path('api/', include('api.urls')),
]
