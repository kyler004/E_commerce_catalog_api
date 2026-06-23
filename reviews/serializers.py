from rest_framework import serializers

from reviews.models import Review


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'body']


class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'body']


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'user_email',
            'rating',
            'title',
            'body',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_email', 'created_at', 'updated_at']
