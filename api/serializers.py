from rest_framework import serializers
from .models import Category, Product, Variant, Inventory

class InventorySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Inventory
        fields = ['quantity', 'last_updated']

class VariantSerializer(serializers.ModelSerializer):
    inventory = InventorySerializer(read_only=True)