from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsEmailVerified
from api.views import StandardPagination
from reviews.models import Review
from reviews.serializers import ReviewCreateSerializer, ReviewSerializer, ReviewUpdateSerializer
from reviews.services import ReviewValidationError, create_review


class ProductReviewListCreateView(APIView):
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsEmailVerified()]

    def get(self, request, product_id):
        queryset = Review.objects.filter(product_id=product_id).select_related('user')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ReviewSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, product_id):
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            review = create_review(request.user, product_id, serializer.validated_data)
        except ReviewValidationError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get_object(self, request, pk):
        try:
            return Review.objects.get(pk=pk, user=request.user)
        except Review.DoesNotExist:
            return None

    def patch(self, request, pk):
        review = self.get_object(request, pk)
        if review is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewUpdateSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReviewSerializer(review).data)

    def delete(self, request, pk):
        review = self.get_object(request, pk)
        if review is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
