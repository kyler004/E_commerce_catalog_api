from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Category, Product, Variant

class ProductFilterTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Electronics")
        
        # Product 1: High price, Red, Large
        self.p1 = Product.objects.create(
            name="Expensive Product", 
            description="High end", 
            price=100.00, 
            category=self.category
        )
        Variant.objects.create(product=self.p1, size="L", color="Red", sku="P1-L-RED")
        
        # Product 2: Low price, Blue, Small
        self.p2 = Product.objects.create(
            name="Cheap Product", 
            description="Low end", 
            price=20.00, 
            category=self.category
        )
        Variant.objects.create(product=self.p2, size="S", color="Blue", sku="P2-S-BLUE")

        # Product 3: Mid price, Red, Small
        self.p3 = Product.objects.create(
            name="Mid Product", 
            description="Mid range", 
            price=50.00, 
            category=self.category
        )
        Variant.objects.create(product=self.p3, size="S", color="Red", sku="P3-S-RED")

    def test_filter_by_price_range(self):
        # Filter products between 30 and 150 (should match p1 and p3)
        response = self.client.get('/api/products/', {'min_price': 30, 'max_price': 150})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        ids = [p['id'] for p in results]
        self.assertIn(self.p1.id, ids)
        self.assertIn(self.p3.id, ids)

    def test_filter_by_color(self):
        # Filter by color Red (should match p1 and p3)
        response = self.client.get('/api/products/', {'color': 'Red'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        ids = [p['id'] for p in results]
        self.assertIn(self.p1.id, ids)
        self.assertIn(self.p3.id, ids)

    def test_filter_by_size(self):
        # Filter by size S (should match p2 and p3)
        response = self.client.get('/api/products/', {'size': 'S'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
        ids = [p['id'] for p in results]
        self.assertIn(self.p2.id, ids)
        self.assertIn(self.p3.id, ids)

    def test_combined_filters(self):
        # Filter: Price < 80 AND Color Red (Should match p3 only)
        response = self.client.get('/api/products/', {'max_price': 80, 'color': 'Red'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.p3.id)
