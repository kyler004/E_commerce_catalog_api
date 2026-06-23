from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsEmailVerified, IsStaff
from promotions.models import Promotion
from promotions.serializers import PromotionSerializer


class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified, IsStaff]
